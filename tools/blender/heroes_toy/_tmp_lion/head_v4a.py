# ---------------------------------------------------------------- head geometry (v4: Hok San frame, built at v2 size then shrunk by HK)
# The head is a rigid frame: a boxy superellipsoid shell sheared so the flat forehead leans back (a wedge from the side),
# a square shovel jaw that juts past it, and directional fur clumps (lip hangs down, brows and rim sweep back).
from mathutils.bvhtree import BVHTree
HC = V((0, .10, 1.98)); HR = V((.70, .44, .46)); HX = (4.0, 5.0, 3.5)   # shell centre, radii, superellipse exponent per axis
LEAN, TAPY, TAPX = .34, .20, .08                                     # forehead lean back, depth taper and width flare with height
JC = V((0, .24, 1.69)); JRO = V((.68, .56, .36)); JRI = V((.60, .48, .29)); JE = 3.2   # shovel jaw centre, outer and inner radii, squareness
JP = V((0, -.20, 1.69))                                          # jaw hinge
JAW0 = 10                                                        # rest pose jaw just parted so the teeth read
HK = .78; HPV = V((0, .15, 1.95)); HOFF = V((0, .03, -.11))      # head shrink, its pivot, and a drop so it sits inside the cloth frame
def HS(p): return HPV + (V(p) - HPV) * HK + HOFF

