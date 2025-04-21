from fastapi import APIRouter, Depends

from iam import conf
from iam.core import auth

# p -> public (no auth needed)
# r -> router
v1_pr = APIRouter(prefix=conf.WEBROOT+'/v1')
v1_r = APIRouter(prefix=conf.WEBROOT+'/v1', dependencies=[Depends(auth.verify_token)])
