# solve the Laplace Beltrami equation on a sphere
# with Dirichlet boundary condition u = 0
from math import pi
# ngsolve stuff
from ngsolve import *
# xfem and trace fem stuff
import libngsxfem_py.xfem as xfem                                 
# for plotting (convergence plots)
import matplotlib.pyplot as plt
# for asking for interactive shell or not
import sys    
# for making a directory (if it doesn't exist)
import os
# For Integration on Interface
from xfem.basics import *
# For LevelSetAdaptationMachinery
from xfem.lsetcurv import *
# For TraceFEM-Integrators (convenience)
from xfem.tracefem import *
# For HDGTraceFEM-Integrators (convenience)
from xfem.hdgtracefem import *

# 3D: circle configuration
def Make3DProblem():
    from netgen.csg import CSGeometry, OrthoBrick, Pnt
    cube = CSGeometry()
    cube.Add (OrthoBrick(Pnt(-1.41,-1.41,-1.41), Pnt(1.41,1.41,1.41)))
    mesh = Mesh (cube.GenerateMesh(maxh=0.5, quad_dominated=False))
    # mesh.Refine()
    # mesh.Refine()
    # mesh.Refine()
    # mesh.Refine()
    # mesh.Refine()

    problem = {"Diffusion" : 1.0,
               "Convection" : None,
               "Reaction" : 1.0,
               "Source" : sin(pi*z)*(pi*pi*(1-z*z)+1)+cos(pi*z)*2*pi*z,
               "Solution" : sin(pi*z),
               "GradSolution" : CoefficientFunction((pi*cos(pi*z)*(-x*z),pi*cos(pi*z)*(-y*z),pi*cos(pi*z)*(1-z*z))),
               "SurfGradSolution" : CoefficientFunction((pi*cos(pi*z)*(-x*z),pi*cos(pi*z)*(-y*z),pi*cos(pi*z)*(1-z*z))),
               "VolumeStabilization" : 1,
               "Levelset" : sqrt(x*x+y*y+z*z)-1,
               "Lambda" : 10,
               "Mesh" : mesh
              }
    return problem;

problemdata = Make3DProblem()
mesh = problemdata["Mesh"]
order = 2
if (problemdata["VolumeStabilization"]):
    static_condensation = True
else:
    static_condensation = False

lsetmeshadap = LevelSetMeshAdaptation(mesh, order=order, threshold=1000, discontinuous_qn=True)

### Setting up discrete variational problem
with TaskManager():
  Vh_l2 = L2(mesh, order=order, dirichlet=[])
  Vh_l2_tr = TraceFESpace(mesh, Vh_l2, problemdata["Levelset"])
  Vh_facet = FacetFESpace(mesh, order=order, dirichlet=[]) #, flags = {"highest_order_dc" : False}
  Vh_facet_tr = TraceFESpace(mesh, Vh_facet, problemdata["Levelset"])
  Vh_tr = FESpace([Vh_l2_tr,Vh_facet_tr])
  
  a = BilinearForm(Vh_tr, symmetric = True, flags = {"eliminate_internal" : static_condensation})
  if (problemdata["Reaction"] != None):
      a.components[0] += TraceMass(problemdata["Reaction"])
  if (problemdata["Diffusion"] != None):
      a += HDGTraceLaplaceBeltrami(problemdata["Diffusion"],
                                   param_IP_edge = problemdata["Lambda"],
                                   param_normaldiffusion = problemdata["VolumeStabilization"],
                                   param_IP_facet = problemdata["Lambda"])
  
  f = LinearForm(Vh_tr)
  if (problemdata["Source"] != None):
      f.components[0] += TraceSource(problemdata["Source"])
  
  c = Preconditioner(a, type="local", flags= { "test" : True })
  
  u = GridFunction(Vh_tr)
  

def SolveProblem():
    with TaskManager():
        
        # Calculation of the deformation:
        deformation = lsetmeshadap.CalcDeformation(problemdata["Levelset"])
        # Applying the mesh deformation
        mesh.SetDeformation(deformation)
        
        Vh_facet.Update()
        Vh_l2.Update()
        Vh_tr.Update()
        
        for i in range(Vh_tr.ndof):
            if (Vh_tr.CouplingType(i) == COUPLING_TYPE.LOCAL_DOF):
                Vh_tr.FreeDofs()[i] = 0
        
        u.Update()
        a.Assemble();
        f.Assemble();
        
        c.Update();
        
        solvea = CGSolver( mat=a.mat, pre=c.mat, complex=False, printrates=False, precision=1e-8, maxsteps=200000)
        
        # solvea = a.mat.Inverse(Vh_tr.FreeDofs())
        # u.vec.data = ainv * f.vec
        
        if static_condensation:
            f.vec.data += a.harmonic_extension_trans * f.vec
        u.vec.data = solvea * f.vec;
        if static_condensation:
            u.vec.data += a.inner_solve * f.vec
            u.vec.data += a.harmonic_extension * u.vec
            
        global last_num_its
        last_num_its = solvea.GetSteps()
        print("nze: " + str(a.mat.AsVector().size))
        print("number of iterations: " + str(last_num_its))
        
        
        coef_error_sqr = (u.components[0] - problemdata["Solution"])*(u.components[0] - problemdata["Solution"])
        l2diff = sqrt(IntegrateOnInterface(lsetmeshadap.lset_p1,mesh,coef_error_sqr,order=2*order+2))
        print("l2diff = {}".format(l2diff))
        mesh.UnsetDeformation()

for i in range(3):
    if (i!=0):
        mesh.Refine()
    SolveProblem()
    RefineAtLevelSet(gf=lsetmeshadap.lset_p1)

    
Draw(u.components[0],mesh,"u",draw_surf=False)

vtk = VTKOutput(ma=mesh,coefs=[lsetmeshadap.lset_p1,lsetmeshadap.deform,u.components[0]],
                names=["lsetp1","deform","u"],filename="vtkout_",subdivision=1)
vtk.Do()


### print hdg-intergrator timers
hdgtimers = [a for a in Timers() if "HDG" in a["name"]]
hdgtimers = sorted(hdgtimers, key=lambda k: k["time"], reverse=True)
for timer in hdgtimers:
    print("{:<45}: {:6} cts, {:.8f} s, {:.6e} s(avg.)"
          .format(timer["name"],timer["counts"],timer["time"],timer["time"]/timer["counts"]))
