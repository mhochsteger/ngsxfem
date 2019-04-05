# unfitted Heat equation with Neumann b.c.
# higher order geometry approximation with space-time mesh transformation
from ngsolve import *
from time import sleep
from netgen.geom2d import unit_square
from netgen.geom2d import SplineGeometry
from netgen.meshing import MeshingParameters

from ngsolve.internal import *
from ngsolve.solvers import *
from ngsolve.meshes import *
from xfem import *
from math import pi
import sys

from xfem.lset_spacetime import *

ngsglobals.msg_level = 1

i = 5
gamma = 2.5

if hasattr(sys, 'argv') and len(sys.argv) == 5 and sys.argv[1] == "i" and sys.argv[3] == "stab":
    i = int(sys.argv[2])
    gamma = float(sys.argv[4])
    print("Sys argv :", sys.argv)
    print("Loading manual val for i, gamma: ", i, gamma)
else:
    print("Loading default val for i, gamma: ", i, gamma)

#square = SplineGeometry()
#square.AddRectangle([-0.6,-1],[0.6,1])
#ngmesh = square.GenerateMesh(maxh=0.5**(i+1), quad_dominated=False)
#mesh = Mesh (ngmesh)

x_len = 0.6
y_len = 1.2
mesh = MakeStructured2DMesh(quads=False,nx=2**(i+1),ny=2**(i+2),mapping= lambda x,y : (2*x_len*x-x_len,2*y_len*y-y_len))

# polynomial order in time
k_t = 2
# polynomial order in space
k_s = k_t
# spatial FESpace for solution
fes1 = H1(mesh, order=k_s)
# polynomial order in time for level set approximation
lset_order_time = k_t
# integration order in time
time_order = 2*k_t
# time finite element (nodal!)
tfe = ScalarTimeFE(k_t) 
# space-time finite element space
st_fes = SpaceTimeFESpace(fes1,tfe, flags = {"dgjumps": True})

#Fitted heat equation example
tstart = 0
tend = 1
delta_t = (tend - tstart)/(2**(i+2))
tnew = 0

told = Parameter(tstart)
tref = ReferenceTimeVariable()
t = told + delta_t*tref

lset_adap_st = LevelSetMeshAdaptation_Spacetime(mesh, order_space = k_s, order_time = lset_order_time,
                                                threshold=0.05, discontinuous_qn=True)

# radius of disk (the geometry)
r0 = 0.5

# position shift of the geometry in time
rho =  CoefficientFunction((1/(pi))*sin(2*pi*t))
rhoL = lambda t:CoefficientFunction((1/(pi))*sin(2*pi*t))
# velocity of position shift
d_rho = CoefficientFunction(2*cos(2*pi*t))
#convection velocity:
w = CoefficientFunction((0,d_rho)) 

# level set
r = sqrt(x**2+(y-rho)**2)
levelset= r - r0

# solution and r.h.s.
Q = pi/r0   
u_exact = cos(Q*r) * sin(pi*t)
u_exactL = lambda t: cos(Q*sqrt(x**2+(y-rhoL(t))**2)) * sin(pi*t)
coeff_f = (Q/r * sin(Q*r) + (Q**2) * cos(Q*r)) * sin(pi*t) + pi * cos(Q*r) * cos(pi*t)


gfu = GridFunction(st_fes)

u_ic = CreateTimeRestrictedGF(gfu,0)
u_last = CreateTimeRestrictedGF(gfu,1.0)
u_first = CreateTimeRestrictedGF(gfu,1.0)

u,v = st_fes.TnT()


lset_p1 = lset_adap_st.lset_p1    


lset_top = CreateTimeRestrictedGF(lset_p1,1.0)
lset_bottom = CreateTimeRestrictedGF(lset_p1,0.0)

dfm = lset_adap_st.deform
dfm_last_top = CreateTimeRestrictedGF(dfm,1.0)
dfm_current_top = CreateTimeRestrictedGF(dfm,1.0)
dfm_current_bottom = CreateTimeRestrictedGF(dfm,0.0)

t_old = tstart

h = specialcf.mesh_size

#Draw(lset_top,mesh,"lset")
#Draw(IfPos(-lset_top,u_exactL(told),float('nan')),mesh,"u_exact")
#Draw(IfPos(-lset_top,u_ic,float('nan')),mesh,"u")

#Draw(dfm,mesh,"dfm")
#Draw(dfm_current_bottom,mesh,"dfm_current_bottom")
#Draw(dfm_current_top,mesh,"dfm_current_top")

#visoptions.deformation = 1

#Draw(h, mesh, "h")

lset_neg = { "levelset" : lset_p1, "domain_type" : NEG, "subdivlvl" : 0}
lset_neg_bottom = { "levelset" : lset_bottom, "domain_type" : NEG, "subdivlvl" : 0}
lset_neg_top = { "levelset" : lset_top, "domain_type" : NEG, "subdivlvl" : 0}

def SpaceTimeNegBFI(form):
    return SymbolicBFI(levelset_domain = lset_neg, form = form, time_order=time_order, definedonelements = ci.GetElementsOfType(HASNEG))

ci = CutInfo(mesh,time_order=time_order)

    
hasneg_integrators_a = []
hasneg_integrators_a_top = []
hasneg_integrators_f = []
hasneg_integrators_f_bottom = []
patch_integrators_a = []


hasneg_integrators_a.append(SpaceTimeNegBFI(form =  -u*(dt(v) + InnerProduct( dt_vec(dfm) , grad(v)) )
                                            + delta_t*grad(u)*grad(v)
                                            - delta_t*u*InnerProduct(w,grad(v))))
#hasneg_integrators_a.append(SpaceTimeNegBFI(form = u*v))
#hasneg_integrators_a.append(SymbolicBFI(levelset_domain = lset_neg_top, form = fix_t(u,1)*fix_t(v,1), deformation = dfm_current_top))
hasneg_integrators_a_top.append(SymbolicBFI(levelset_domain = lset_neg_top, form = fix_t(u,1)*fix_t(v,1)))

patch_integrators_a.append(SymbolicFacetPatchBFI(form = 4**(i-4)*delta_t*(1+delta_t/h)*gamma*(u-u.Other())*(v-v.Other()), skeleton=False, time_order=time_order))
hasneg_integrators_f.append(SymbolicLFI(levelset_domain = lset_neg, form = delta_t*coeff_f*v, time_order=time_order)) 
#hasneg_integrators_f.append(SymbolicLFI(levelset_domain = lset_neg_bottom, form = u_ic*fix_t(v,0), deformation = dfm_current_bottom))
hasneg_integrators_f_bottom.append(SymbolicLFI(levelset_domain = lset_neg_bottom,form = u_ic*fix_t(v,0)))

outfile = open("errorp"+str(k_t)+"_dev_i"+str(i)+"_gamma"+str(gamma)+".dat", "w")

l2max = 0
l2_timeintmax = 0

while tend - t_old > delta_t/2:
    # update lset geometry to new time slab (also changes lset_p1 !)
    #dfm = lset_adap_st.CalcDeformation(levelset,told,t_old,delta_t)
    #with TaskManager():
    dfm = lset_adap_st.CalcDeformation(levelset,tref,t_old,delta_t)
    
    RestrictGFInTime(spacetime_gf=lset_p1,reference_time=0.0,space_gf=lset_bottom)
    RestrictGFInTime(spacetime_gf=lset_p1,reference_time=1.0,space_gf=lset_top)
    RestrictGFInTime(spacetime_gf=dfm,reference_time=0.0,space_gf=dfm_current_bottom)   
    RestrictGFInTime(spacetime_gf=dfm,reference_time=1.0,space_gf=dfm_current_top)   

    if t_old == tstart:
    #if True:
        mesh.SetDeformation(dfm_current_bottom)
        u_ic.Set(CoefficientFunction(u_exactL(tstart)))
        #u_ic.Set(CoefficientFunction(u_exactL(t_old)))
        mesh.UnsetDeformation()
    else:
        u_ic.Set(shifted_eval(u_last, back = dfm_last_top, forth = dfm_current_bottom))


    # update markers in (space-time) mesh
    ci.Update(lset_p1,time_order=time_order)

    # re-compute the facets for stabilization:
    ba_facets = GetFacetsWithNeighborTypes(mesh,a=ci.GetElementsOfType(HASNEG),
                                                b=ci.GetElementsOfType(IF))
    # re-evaluate the "active dofs" in the space time slab
    active_dofs = GetDofsOfElements(st_fes,ci.GetElementsOfType(HASNEG))

    # re-set definedonelements-markers according to new markings:
    for integrator in hasneg_integrators_a +hasneg_integrators_a_top + hasneg_integrators_f + hasneg_integrators_f_bottom:
        integrator.SetDefinedOnElements(ci.GetElementsOfType(HASNEG))
    for integrator in patch_integrators_a:
        integrator.SetDefinedOnElements(ba_facets)

    #a = BilinearForm(st_fes,check_unused=False,symmetric=False)
    a = RestrictedBilinearForm(st_fes,"a", ci.GetElementsOfType(HASNEG), ba_facets, check_unused=False)
    for integrator in hasneg_integrators_a + patch_integrators_a:
        a += integrator
    
    a_top = RestrictedBilinearForm(st_fes,"a_top", ci.GetElementsOfType(HASNEG), ba_facets, check_unused=False)
    for integrator in hasneg_integrators_a_top:
        a_top += integrator
    
    #a_no_dfm = RestrictedBilinearForm(st_fes,"a_no_dfm", ci.GetElementsOfType(HASNEG), ba_facets, check_unused=False)
    #for integrator in patch_integrators_a:
        #a_no_dfm += integrator
    
    f = LinearForm(st_fes)
    for integrator in hasneg_integrators_f:
        f += integrator

    f_bottom = LinearForm(st_fes)
    for integrator in hasneg_integrators_f_bottom:
        f_bottom += integrator
    
    #a_no_dfm.Assemble()
    
    # update mesh deformation and assemble linear system
    mesh.SetDeformation(dfm)
    #with TaskManager():
    a.Assemble()
    f.Assemble()
    mesh.UnsetDeformation()
    
    mesh.SetDeformation(dfm_current_bottom)
    f_bottom.Assemble()
    mesh.UnsetDeformation()
    
    mesh.SetDeformation(dfm_current_top)
    a_top.Assemble()
    mesh.UnsetDeformation()
    
    a.mat.AsVector().data = a.mat.AsVector() + a_top.mat.AsVector() #+ a_no_dfm.mat.AsVector()
    f.vec.data = f.vec + f_bottom.vec
    
    # solve linear system
    #pre = a.mat.Inverse(active_dofs,"umfpack")
    #inv = CGSolver(a.mat, pre, printrates=True, precision=1e-10, maxsteps=15)
    #inv = GMRESSolver(mat=a.mat,pre=pre,printrates=True,precision=1e-8,maxsteps=15)
    inv = a.mat.Inverse(active_dofs,inverse="umfpack")
    gfu.vec.data = inv* f.vec.data
    #gfu.vec.data = GMRes( a.mat, f.vec, pre, tol=1e-20, printrates=True)
    
    #tmp = f.vec.CreateVector()
    #for it in range(5):
    #tmp.data = f.vec.data - a.mat * gfu.vec.data
    #print("Norm of tmp: ", Norm(tmp))
        #gfu.vec.data = gfu.vec.data + inv * tmp.data
    
    # evaluate upper trace of solution for
    #  * for error evaluation 
    #  * upwind-coupling to next time slab
    RestrictGFInTime(spacetime_gf=gfu,reference_time=1.0,space_gf=u_last)
    
    # compute error at final time
    mesh.SetDeformation(dfm_current_top)
    l2error = sqrt(Integrate({ "levelset" : lset_top, "domain_type" : NEG}, (u_exactL(t_old + delta_t) - u_last)**2, mesh, order=2*k_s))
    mesh.UnsetDeformation()
    
    mesh.SetDeformation(dfm)
    l2error_time_int = sqrt(Integrate({ "levelset" : lset_top, "domain_type" : NEG}, (u_exactL(t) - gfu)**2, mesh, order=2*k_s, time_order=time_order))
    mesh.UnsetDeformation()
    
    # update time variable (float and ParameterCL)
    t_old = t_old + delta_t
    told.Set(t_old)
    
    #Draw(lset_top, mesh, "lset_top")
    #Draw(lset_bottom, mesh, "lset_bottom")
    #Draw(IfPos(-lset_top,(u_exactL(told)-u_last)**2,float('nan')),mesh,"error")
    #nf = IndicatorCF( mesh=mesh, ba=ci.GetElementsOfType(HASNEG))
    #Draw( nf, mesh, "NEG")
    
    
    # print time and error
    #print("\rt = {0:10}, l2error = {1:20}".format(t_old,l2error),end="")
    print("t = ",t_old, " l2error = ",l2error, " time int L2: ", l2error_time_int)
    #outfile.write(str(t_old)+"\t"+str(l2error)+"\t"+str(Norm(tmp))+"\n")
    outfile.write(str(t_old)+"\t"+str(l2error)+"\t"+str(l2error_time_int)+"\n")
    
    #least_abs_lset_val = 10.
    #for v in lset_p1.vec:
        #if abs(v) < least_abs_lset_val:
            #least_abs_lset_val = abs(v)
    
    #print("least abs: \t\t\t\t\t\t", least_abs_lset_val)
    
    if l2error > l2max:
        l2max = l2error
    if l2error_time_int > l2_timeintmax:
        l2_timeintmax = l2error_time_int
    
    # Redraw:
    #Redraw(blocking=True)

    # store deformation at top level of for next time step
    dfm_last_top.vec.data = dfm_current_top.vec

print("L2 max: ", l2max, " Time int: ", l2_timeintmax)
