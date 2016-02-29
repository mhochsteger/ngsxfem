geometry = d01_testgeom.in2d
#mesh = d08_ref.vol.gz
mesh = d09_simple.vol.gz
#mesh = d04_refined_0_05.vol.gz
#mesh = d08_fine.vol.gz
#mesh = d04_unstr.vol.gz
# mesh = d99_testgeom_unstr.vol.gz
shared = libngsxfem_xfem
shared = libngsxfem_lsetcurving

flags tracer = -max_size=0
        
define constant order_deform = "3"
define constant order_qn = "1"
define constant order_lset = "3"
define constant order_scalar = "3"

constant levelset_lower_bound = "-0.0"
constant levelset_upper_bound = "0.0"
constant lset_lower_bound = -0
constant lset_upper_bound = 0
        
constant one = 1.0
# constant threshold = "0.1"
        #0.5/$(order_deform)
# constant threshold = 0.1
        
define constant heapsize = 1e9
constant R = 2.0/3.0

constant omega = 5.0
constant omega2 = (pi)
constant x0 = 0.0
constant y0 = 0.0
constant r0 = 0.6

define coefficient lset
(
 sqrt((x-x0)*(x-x0)+(y-y0)*(y-y0))-r0
)
        
### project level set function into a finite element space of order k
fespace fes_ho -type=h1ho -order=$(order_lset)
gridfunction lset_ho -fespace=fes_ho

numproc setvalues npsv -gridfunction=lset_ho -coefficient=lset

###########################################################################
########################### quasi-normal field ############################
###########################################################################

fespace fes_normal -type=h1ho -order=$(order_qn) -vec #-dirichlet=[1,2,3,4,5,6]
gridfunction qn -fespace=fes_normal
        
numproc setvalues npsv -gridfunction=qn -coefficient=grad_lset_ho 
        
### project this level set function into a finite element space of order 1
fespace fes_p1 -type=h1ho -order=1
gridfunction lset_p1 -fespace=fes_p1

numproc interpolatep1 npipp1b -gridfunction_ho=lset_ho -gridfunction_p1=lset_p1

### determine the deformation 
fespace fes_deform -type=h1ho -order=$(order_deform) -vec -dirichlet=[1,2,3,4]
        
gridfunction deform -fespace=fes_deform

numproc projectshift nppsh -levelset=lset_ho -levelset_p1=lset_p1 -deform=deform -quasinormal=qn -lset_lower_bound=$(lset_lower_bound) -lset_upper_bound=$(lset_upper_bound) -threshold=0.2
        

# numproc levelsetrefine nplsref -levelset=lset_p1

numproc calcerrors npcalcerr -levelset_ho=lset -levelset_p1=lset_p1 -quasinormal=qn -deform=deform
                -lset_lower_bound=$(levelset_lower_bound)
                -lset_upper_bound=$(levelset_upper_bound)
                -only_distance
#                 -refine_threshold=0.05


numproc visualization npvis -scalarfunction=lset_p1 -vectorfunction=deform -deformationscale=1 -subdivision=0  -minval=0.0 -maxval=0.0 -nolineartexture

        
        

























numproc setdeformation npudef -gridfunction=deform



# general constants
define constant zero = 0.0
define constant one = 1.0
define constant two = 2.0

define constant C1 = 1.0
define constant C2 = 4.0


# henry weights
define constant bneg = 1.0
define constant bpos = 1.5

define constant aneg = 2.0
define constant apos = 1.0

define constant abneg = (aneg*bneg)
define constant abpos = (apos*bpos)

define coefficient r
(sqrt(x*x+y*y)),

define coefficient Ur
(cos(pi*r*r/(2*r0*r0))),

define coefficient MLapUr
(
  cos(pi*r*r/(2*r0*r0)) * (pi*pi*r*r)/(r0*r0*r0*r0) + sin(pi*r*r/(2*r0*r0)) * 2.0*pi/(r0*r0)
),
                        
define coefficient solpos
(aneg*Ur+bneg),

define coefficient solneg
(apos*Ur+bpos),

define coefficient rhspos
(abpos*aneg*MLapUr),

define coefficient rhsneg
(abneg*apos*MLapUr),

define constant lambda = 10

define fespace fescomp
       -type=xstdfespace
       -order=$(order_scalar)
       -dirichlet=[1,2]
       -ref_space=0
       # -empty
       #-dgjumps

numproc informxfem npix 
        -xstdfespace=fescomp
        -coef_levelset=lset

define gridfunction u -fespace=fescomp

define linearform f -fespace=fescomp # -print
xsource rhsneg rhspos
#xsource solneg solpos

define bilinearform a -fespace=fescomp #-printelmat -elmatev #-print
xlaplace abneg abpos
xnitsche_heaviside aneg apos bneg bpos lambda

#xmass one one         
# lo_ghostpenalty aneg apos one
# sec_ghostpenalty aneg apos one

numproc setvaluesx npsvx -gridfunction=u -coefficient_neg=solpos -coefficient_pos=solpos -boundary -print

#define preconditioner c -type=local -bilinearform=a -test -block
define preconditioner c -type=direct -bilinearform=a #-inverse=sparsecholesky#-test
#define preconditioner c -type=bddc -bilinearform=a -test -block

##define preconditioner c -type=multigrid -bilinearform=a -test #-smoother=block

numproc bvp npbvp -gridfunction=u -bilinearform=a -linearform=f -solver=cg -preconditioner=c -maxsteps=10 -prec=1e-16 # -print

define coefficient veczero
(0,0),

numproc xdifference npxd 
        -solution=u 
        -solution_n=solneg
        -solution_p=solpos
        -levelset=lset
        -interorder=8
        -henryweight_n=1
        -henryweight_p=1.5
        -diffusion_n=1
        -diffusion_p=1



numproc unsetdeformation npudef














        






                
# define fespace fesustd
#         -type=h1ho
#         -order=$(order)

# define fespace fesunegpos
#         -type=compound
#         -spaces=[fesustd,fesustd]
        
# define gridfunction gf_u_negpos -fespace=fesunegpos -novisual

# numproc xtonegpos npxtonegposp -xstd_gridfunction=u -negpos_gridfunction=gf_u_negpos
        
# numproc vtkoutput npout -filename=d08_output_sd2_
#         -coefficients=[lset]
#         -gridfunctions=[gf_u_negpos.1,gf_u_negpos.2]
#         -fieldnames=[levelset,uneg,upos]
#         -subdivision=2
                