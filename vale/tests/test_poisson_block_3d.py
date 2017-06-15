# coding: utf-8

from vale import ValeCodegen
from vale import ValeParser
from vale import construct_model

from sympy import S
from sympy.core.sympify import sympify
import numpy as np

# ...
def run(filename):
    # ...
    from caid.cad_geometry import cube
    geometry = cube()

    from clapp.spl.mapping import Mapping
    mapping = Mapping(geometry=geometry)
    # ...

    # ... creates discretization parameters
    from clapp.disco.parameters.bspline import BSpline

    bspline_params = BSpline([8,8,8], [2,2,2], \
                             bc_min=[0,0,0], \
                             bc_max=[0,0,0])
    # ...

    # ... create a context from discretization
    from clapp.fema.context        import Context

    context = Context(dirname="input", \
                      discretization_params=bspline_params)
    # ...

    # ...
    pde = construct_model(filename, backend="clapp", \
                          context=context, mapping=mapping)
    # ...

    # ... accessing the pde declarations
    V           = pde["V"]
    phi         = pde["phi"]
    psi         = pde["psi"]
    form_a      = pde["a"]
    form_b      = pde["b"]
    f           = pde["f"]
    g           = pde["g"]
    # ...

    # ...
    assembler_a = form_a.assembler
    matrix      = form_a.matrix
    assembler_b = form_b.assembler
    rhs         = form_b.vector
    # ...

    # ... set expression for the function f
    f.set("2*x*(1-x)*y*(1-y) + 2*y*(1-y)*z*(1-z) + 2*z*(1-z)*x*(1-x)")
    # ...

    # ... set expression for the function g
    g.set("4*x*(1-x)*y*(1-y) + 4*y*(1-y)*z*(1-z) + 4*z*(1-z)*x*(1-x)")
    # ...

    # ...
    assembler_b.assemble()
    assembler_a.assemble()
    # ...

    # ...
    from clapp.plaf.parameters.linear_solver import PACK_GMRES
    from clapp.plaf.parameters.linear_solver import DRIVER
    from clapp.plaf.linear_solver  import Linear_solver

    params = DRIVER(solver=PACK_GMRES())
    linsol = Linear_solver(matrix=matrix, dirname="input", parameters=params)
    # ...

    # ...
    z = rhs.get(as_matrix=False)
    y = linsol.solve(z)
    # ...

    # ... we use the rhs to retrieve the solution as blocks
    rhs.set(y)
    y = rhs.get(as_matrix=True)

    phi.set(y[0,:])
    psi.set(y[1,:])
    # ...

    # ... exports phi to vtk file. Can be used in Visit and Paraview
    filename_out = "phi_3d_"+filename.split('/')[-1].split('.')[0] + ".vtk"
    phi.to_vtk(filename_out, mapping=mapping, n_pts=20)

    filename_out = "psi_3d_"+filename.split('/')[-1].split('.')[0] + ".vtk"
    psi.to_vtk(filename_out, mapping=mapping, n_pts=20)
    # ...

    # ... define the analytical solution for phi
    from clapp.vale.expressions.function import Function

    phi_analytic = Function("phi_analytic", "x*(1-x)*y*(1-y)*z*(1-z)", args=["x", "y", "z"])
    psi_analytic = Function("psi_analytic", "2*x*(1-x)*y*(1-y)*z*(1-z)", args=["x", "y", "z"])
    # ...

    # ... compute L2 error
    x = phi.compute_l2_error(mapping=mapping, function=phi_analytic)[0,0]
    print ("    L2-error norm (phi): " + str(x))

    x = psi.compute_l2_error(mapping=mapping, function=psi_analytic)[0,0]
    print ("    L2-error norm (psi): " + str(x))
    # ...

    # ...
    cmd = "rm -rf input"
    os.system(cmd)
    # ...

    print ("> run using " + str(filename) + " passed.")
    # ...
# ...

import clapp.common.utils      as clapp_utils

# ... initializing Clapp
clapp_utils.initialize()
# ...

import os

cmd = "rm -rf input"
os.system(cmd)

run(filename="inputs/3d/poisson_block.vl")

cmd = "rm -rf input"
os.system(cmd)

# ... Finalizing Clapp
clapp_utils.finalize()
# ...