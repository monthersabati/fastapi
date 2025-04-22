import re
import logging
import requests
from functools import lru_cache
from async_lru import alru_cache
from keystoneauth1 import session, token_endpoint
from keystoneauth1.identity import v3 as v3_auth
from keystoneclient.v3 import client as v3_client
from keystoneauth1 import exceptions as keystone_exceptions

from iam import conf
from iam import exceptions

LOG = logging.getLogger(__name__)


def _get_session(**kwargs):
    insecure = conf.OPENSTACK_SSL_NO_VERIFY
    verify = conf.OPENSTACK_SSL_CACERT

    if insecure:
        verify = False

    return session.Session(verify=verify, **kwargs)

async def _get_access_info(keystone_auth):
    """Get the access info from an unscoped auth

    This function provides the base functionality that the
    plugins will use to authenticate and get the access info object.

    :param keystone_auth: keystoneauth1 identity plugin
    :raises: exceptions.KeystoneAuthException on auth failure
    :returns: keystoneclient.access.AccessInfo
    """
    session = _get_session()

    try:
        unscoped_auth_ref = keystone_auth.get_access(session)
    except keystone_exceptions.ConnectFailure as exc:
        LOG.error(str(exc))
        msg = 'Unable to establish connection to keystone endpoint.'
        raise exceptions.KeystoneAuthException(msg)
    except (keystone_exceptions.Unauthorized,
            keystone_exceptions.Forbidden,
            keystone_exceptions.NotFound) as exc:
        msg = str(exc)
        LOG.debug(msg)
        match = re.match(r"The password is expired and needs to be changed"
                            r" for user: ([^.]*)[.].*", msg)
        if match:
            exc = exceptions.KeystoneAuthException('Password expired.')
            exc.user_id = match.group(1)
            raise exc
        msg = 'Invalid credentials.'
        raise exceptions.KeystoneCredentialsException(msg)
    except (keystone_exceptions.ClientException,
            keystone_exceptions.AuthorizationFailure) as exc:
        msg = ("An error occurred authenticating. "
                "Please try again later.")
        LOG.debug(str(exc))
        raise exceptions.KeystoneAuthException(msg)
    return unscoped_auth_ref

def _get_token_auth_plugin(auth_url, token, project_id=None, domain_name=None):
    if domain_name:
        return v3_auth.Token(auth_url=auth_url,
                             token=token,
                             domain_name=domain_name,
                             reauthenticate=False)
    else:
        return v3_auth.Token(auth_url=auth_url,
                             token=token,
                             project_id=project_id,
                             reauthenticate=False)

async def _get_project_scoped_auth(unscoped_auth, unscoped_auth_ref, recent_project=None):
    """Get the project scoped keystone auth and access info

    This function returns a project scoped keystone token plugin
    and AccessInfo object.

    :param unscoped_auth: keystone auth plugin
    :param unscoped_auth_ref: keystoneclient.access.AccessInfo` or None.
    :param recent_project: project that we should try to scope to
    :return: keystone token auth plugin, AccessInfo object
    """
    auth_url = unscoped_auth.auth_url
    session = _get_session()

    def _list_projects(session, auth_plugin, auth_ref=None):
        try:
            client = v3_client.Client(session=session, auth=auth_plugin)
            if auth_ref.is_federated:
                return client.federation.projects.list()
            else:
                return client.projects.list(user=auth_ref.user_id)

        except (keystone_exceptions.ClientException,
                keystone_exceptions.AuthorizationFailure):
            msg = 'Unable to retrieve authorized projects.'
            raise exceptions.KeystoneRetrieveProjectsException(msg)

    projects = _list_projects(session, unscoped_auth, unscoped_auth_ref)
    # Attempt to scope only to enabled projects
    projects = [project for project in projects if project.enabled]

    # if a most recent project was found, try using it first
    if recent_project:
        for pos, project in enumerate(projects):
            if project.id == recent_project or project.name == recent_project:
                # move recent project to the beginning
                projects.pop(pos)
                projects.insert(0, project)
                break

    scoped_auth = None
    scoped_auth_ref = None
    for i, project in enumerate(projects):
        token = unscoped_auth_ref.auth_token
        scoped_auth = _get_token_auth_plugin(auth_url, token=token, project_id=project.id)
        try:
            scoped_auth_ref = scoped_auth.get_access(session)
            if recent_project and i > 0 and conf.OPENSTACK_OWNER_ROLE not in scoped_auth_ref.role_names:
                continue
        except (keystone_exceptions.ClientException,
                keystone_exceptions.AuthorizationFailure):
            LOG.info('Attempted scope to project %s failed, will attempt '
                        'to scope to another project.', project.name)
        else:
            break

    return scoped_auth, scoped_auth_ref

async def authenticate(unscoped_token=None, username=None, password=None, **kwargs):
    auth_url = conf.OPENSTACK_KEYSTONE_URL
    default_domain = conf.OPENSTACK_KEYSTONE_DEFAULT_DOMAIN

    if unscoped_token:
        unscoped_auth = v3_auth.Token(
            auth_url=auth_url,
            token=unscoped_token,
            reauthenticate=False,
        )
    else:
        unscoped_auth = v3_auth.Password(
            auth_url=auth_url,
            username=username,
            password=password,
            user_domain_name=default_domain,
            unscoped=True
        )

    recent_project = kwargs.get('project') or username

    try:
        unscoped_auth_ref = await _get_access_info(unscoped_auth)
        scoped_auth, scoped_auth_ref = await _get_project_scoped_auth(
            unscoped_auth, unscoped_auth_ref, recent_project=recent_project)
    except:
        msg = 'Invalid Username or Password.'
        raise exceptions.KeystoneAuthException(msg)

    return {'scoped_token': scoped_auth_ref.auth_token, 'unscoped_token': unscoped_auth_ref.auth_token}

@alru_cache
async def token_validate(token):
    url = f"{conf.OPENSTACK_KEYSTONE_URL}/auth/tokens"
    headers = {
        "X-Auth-Token": token,
        "X-Subject-Token": token
    }
    response = requests.get(url, headers=headers)
    if response.ok:
        result = response.json().get('token')
        for field in ('methods', 'audit_ids', 'catalog'):
            result.pop(field, None)
        result['token'] = token
        return result

@lru_cache
def get_client(request):
    user = request.state.user
    token_id = user.token

    cache_attr = "_keystoneclient"
    if hasattr(request.state, cache_attr):
        conn = getattr(request, cache_attr)
    else:
        auth_url = conf.OPENSTACK_KEYSTONE_URL
        verify = not conf.OPENSTACK_SSL_NO_VERIFY
        cacert = conf.OPENSTACK_SSL_CACERT
        verify = verify and cacert
        remote_addr = request.client.host
        token_auth = token_endpoint.Token(endpoint=auth_url, token=token_id)
        keystone_session = session.Session(auth=token_auth, original_ip=remote_addr, verify=verify)
        conn = v3_client.Client(session=keystone_session, debug=conf.DEBUG)
        setattr(request, cache_attr, conn)
    return conn

async def tenant_list(request, domain=None, user=None, filters=None):
    client = get_client(request)
    manager = client.projects
    tenants = []
    kwargs = {
        "domain": domain,
        "user": user
    }
    if filters is not None:
        kwargs.update(filters)
    tenants = manager.list(**kwargs)
    return tenants

async def tenant_create(request, name, description=None, enabled=None,
                  domain=None, **kwargs):
    client = get_client(request)
    manager = client.projects
    return manager.create(name, domain,
                            description=description,
                            enabled=enabled, **kwargs)

async def tenant_get(request, project):
    client = get_client(request)
    manager = client.projects
    return manager.get(project)

async def tenant_update(request, project, name=None, description=None,
                  enabled=None, domain=None, **kwargs):
    client = get_client(request)
    manager = client.projects
    return manager.update(project, name=name, description=description,
                            enabled=enabled, domain=domain, **kwargs)

async def tenant_delete(request, project):
    client = get_client(request)
    manager = client.projects
    manager.delete(project)

async def user_list(request, project=None, domain=None, group=None, filters=None):
    client = get_client(request)
    manager = client.users
    kwargs = {
        "project": project,
        "domain": domain,
        "group": group
    }
    if filters is not None:
        kwargs.update(filters)
    return manager.list(**kwargs)

async def user_create(request, name=None, email=None, password=None, project=None,
                enabled=None, domain=None, description=None, **data):
    client = get_client(request)
    manager = client.users
    user = manager.create(name, password=password, email=email,
                            default_project=project, enabled=enabled,
                            domain=domain, description=description,
                            **data)
    return user

async def user_get(request, user_id):
    client = get_client(request)
    manager = client.users
    return manager.get(user_id)

async def user_update(request, user, **data):
    client = get_client(request)
    manager = client.users
    return manager.update(user, **data)

async def user_delete(request, user_id):
    client = get_client(request)
    manager = client.users
    manager.delete(user_id)

async def group_list(request, domain=None, project=None, user=None, filters=None):
    client = get_client(request)
    manager = client.groups
    groups = []
    kwargs = {
        "domain": domain,
        "user": user,
        "name": None
    }
    if filters is not None:
        kwargs.update(filters)
    
    groups = manager.list(**kwargs)

    if project:
        project_groups = []
        for group in groups:
            roles = await role_list(request, filters={'group': group.id, 'project': project})
            if roles:
                project_groups.append(group)
        groups = project_groups
    return groups

async def group_create(request, name, description=None, domain=None):
    client = get_client(request)
    manager = client.groups
    return manager.create(name=name,
                            description=description,
                            domain=domain)

async def group_get(request, group_id, admin=True):
    client = get_client(request)
    manager = client.groups
    return manager.get(group_id)

async def group_update(request, group_id, name=None, description=None):
    client = get_client(request)
    manager = client.groups
    return manager.update(group=group_id,
                            name=name,
                            description=description)
    
async def group_delete(request, group_id):
    client = get_client(request)
    manager = client.groups
    return manager.delete(group_id)

async def group_add_user(request, group, user):
    client = get_client(request)
    manager = client.users
    return manager.add_to_group(group=group, user=user)

async def group_remove_user(request, group, user):
    client = get_client(request)
    manager = client.users
    return manager.remove_from_group(group=group, user=user)

async def role_list(request, filters=None):
    client = get_client(request)
    manager = client.roles
    roles = []
    kwargs = {}
    if filters is not None:
        kwargs.update(filters)
    return manager.list(**kwargs)

async def role_create(request, name):
    client = get_client(request)
    manager = client.roles
    return manager.create(name)

async def role_get(request, role_id):
    client = get_client(request)
    manager = client.roles
    return manager.get(role_id)

async def role_update(request, role_id, name=None):
    client = get_client(request)
    manager = client.roles
    return manager.update(role_id, name)

async def role_delete(request, role_id):
    client = get_client(request)
    manager = client.roles
    manager.delete(role_id)

async def role_assignments_list(request, project=None, user=None, role=None,
                          group=None, domain=None, effective=False,
                          include_subtree=True, include_names=False):
    client = get_client(request)
    manager = client.role_assignments
    if include_subtree:
        domain = None
    return manager.list(project=project, user=user, role=role, group=group,
                        domain=domain, effective=effective,
                        include_subtree=include_subtree,
                        include_names=include_names)

async def role_assignment_create(request, role, project=None, user=None,
                         group=None, domain=None):
    client = get_client(request)
    manager = client.roles
    manager.grant(role, user=user, project=project,
                  group=group, domain=domain)

async def role_assignment_delete(request, role, project=None, user=None,
                            group=None, domain=None):
    client = get_client(request)
    manager = client.roles
    return manager.revoke(role, user=user, project=project,
                          group=group, domain=domain)
    
