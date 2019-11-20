"""
	Description:
	------------
	Two disjoint triangles.
"""

from netgen.geom2d import SplineGeometry
from ngsolve import *
from xfem import *

geo = SplineGeometry()
geo.AddRectangle((-4, -3), (4, 3), bc=1)

mesh = Mesh(geo.GenerateMesh(maxh=0.5))



V = H1(mesh,order=1)
lsetp1_t1_1, lsetp1_t1_2, lsetp1_t1_3 = GridFunction(V), GridFunction(V),\
										GridFunction(V)

lsetp1_t2_1, lsetp1_t2_2, lsetp1_t2_3 = GridFunction(V), GridFunction(V),\
										GridFunction(V)

InterpolateToP1( x     - 3, lsetp1_t1_1)
InterpolateToP1(-x - y + 1, lsetp1_t1_2)
InterpolateToP1(-x + y + 1, lsetp1_t1_3)
InterpolateToP1(-x     - 3, lsetp1_t2_1)
InterpolateToP1( x - y + 1, lsetp1_t2_2)
InterpolateToP1( x + y + 1, lsetp1_t2_3)

Draw(lsetp1_t1_1, mesh, "lsetp1_t1_1")
Draw(lsetp1_t1_2, mesh, "lsetp1_t1_2")
Draw(lsetp1_t1_3, mesh, "lsetp1_t1_3")
Draw(lsetp1_t1_1 * lsetp1_t1_2 * lsetp1_t1_3, mesh, "lsetp1_t1_mult")

Draw(lsetp1_t2_1, mesh, "lsetp1_t2_1")
Draw(lsetp1_t2_2, mesh, "lsetp1_t2_2")
Draw(lsetp1_t2_3, mesh, "lsetp1_t2_3")
Draw(lsetp1_t2_1 * lsetp1_t2_2 * lsetp1_t2_3, mesh, "lsetp1_t2_mult")


inner1 = {"levelsets": (lsetp1_t1_1,lsetp1_t1_2,lsetp1_t1_3),
		  "domain_type": (NEG,NEG,NEG)
		 }

boundary1 = {"levelsets": (lsetp1_t1_1,lsetp1_t1_2,lsetp1_t1_3)
		     "domain_type": (IF,NEG,NEG)|(NEG,IF,NEG)|(NEG,NEG,IF)
			}

outer1 = {"levelsets": (lsetp1_t1_1,lsetp1_t1_2,lsetp1_t1_3),
		  "domain_type": ~(NEG,NEG,NEG)
		 }

inner2 = {"levelsets": (lsetp1_t2_1,lsetp1_t2_2,lsetp1_t2_3),
		  "domain_type": (NEG,NEG,NEG)
		 }

boundary2 = {"levelsets": (lsetp1_t2_1,lsetp1_t2_2,lsetp1_t2_3)
		     "domain_type": (IF,NEG,NEG)|(NEG,IF,NEG)|(NEG,NEG,IF)
			}

outer2 = {"levelsets": (lsetp1_t2_1,lsetp1_t2_2,lsetp1_t2_3),
		  "domain_type": ~(NEG,NEG,NEG)
		 }

# Best way to do "outside of both"?

ouside_of_both = {"levelsets": (lsetp1_t1_1,lsetp1_t1_2,lsetp1_t1_3,
								lsetp1_t2_1,lsetp1_t2_2,lsetp1_t2_3),
		  		  "domain_type": ~(NEG,NEG,NEG,ANY,ANY,ANY)&~(ANY,ANY,ANY,NEG,NEG,NEG)
		 		  }

# I would prefer something like

outside_of_both = outer1 & outer2