#! /bin/bash
set -e

# 38 39

export ORIGINAL_PATH="$PATH"
for pyversion in 310
do
    #export pyversion=310
    export PYDIR="/opt/python/cp${pyversion}-cp${pyversion}/bin"
    $PYDIR/python .ci/versions_to_files.py
    export NGSOLVE_VERSION=`cat ngsolve.version`
    export PATH="ORIGINAL_$PATH:$PYDIR"
    pip install ngsolve
    #RUN $PYDIR/pip install -vvv .
    pip wheel -vvv .
    rm -rf _skbuild

    # avx2 build:
    pip uninstall -y netgen-mesher
    pip uninstall -y ngsolve
    
    pip install ngsolve-avx2==$NGSOLVE_VERSION
    NETGEN_ARCH=avx2 pip wheel -vvv .
    
done
python .ci/fix_auditwheel_policy.py
auditwheel repair *.whl
rm *.whl

pip install -U twine
#twine upload wheelhouse/*manylinux*.whl
