from openmm.app import *
from openmm import *
from openmm.unit import nanometer, kelvin, picosecond, picoseconds
from sys import stdout
import argparse
from typing import List

# We're going to always save checkpoints to the same file
checkpoint_file = "checkpoint.chk"
output_file = "final_state.pdb"

# We're going to define a function that will run the simulation according
# to the parameters we pass in
def run_simulation(
    input_pdb: str,
    force_fields: List[str],
    nonbonded_cutoff_nm: int,
    temperature_k: int,
    friction_coeff_ps: int,
    step_size_ps: float,
    checkpoint_steps: int,
    total_steps: int,
):
    pdb = PDBFile(input_pdb)
    forcefield = ForceField(*force_fields)
    system = forcefield.createSystem(
        pdb.topology,
        nonbondedMethod=PME,
        nonbondedCutoff=nonbonded_cutoff_nm * nanometer,
        constraints=HBonds,
    )
    integrator = LangevinMiddleIntegrator(
        temperature_k * kelvin,
        friction_coeff_ps / picosecond,
        step_size_ps * picoseconds,
    )
    simulation = Simulation(pdb.topology, system, integrator)
    
    # We're going to check if a checkpoint file exists, and if it does, we're going to
    # load the simulation from that checkpoint. If it doesn't, we're going to start a new
    # simulation
    if os.path.exists(checkpoint_file):
        print(f"Resuming simulation from checkpoint: {checkpoint_file}")
        simulation.loadCheckpoint(checkpoint_file)
        steps_completed = simulation.currentStep
        steps_remaining = total_steps - steps_completed
    else:
        print("Starting new simulation")
        simulation.context.setPositions(pdb.positions)
        simulation.minimizeEnergy()
        steps_remaining = total_steps
    simulation.reporters.append(
        StateDataReporter(
            stdout, checkpoint_steps, step=True, potentialEnergy=True, temperature=True
        )
    )
    simulation.reporters.append(CheckpointReporter(checkpoint_file, checkpoint_steps))
    print(f"Running simulation for {steps_remaining} steps")
    simulation.step(steps_remaining)
    
    # We're going to save the final state of the simulation to a PDB file
    positions = simulation.context.getState(getPositions=True).getPositions()
    with open(output_file, "w") as f:
        PDBFile.writeFile(simulation.topology, positions, f)

# We're going to define an argument parser to parse the command line arguments.
# This will let us run this script in a customizable way.
parser = argparse.ArgumentParser()
parser.add_argument("--input_pdb", type=str, help="Input PDB file", required=True)
parser.add_argument(
    "--force_fields",
    type=str,
    nargs="+",
    help="Force fields to use",
    required=True,
)
parser.add_argument(
    "--nonbonded_cutoff_nm",
    type=int,
    help="Forcefield system Nonbonded cutoff in nanometers",
    required=True,
)
parser.add_argument(
    "--temperature_k",
    type=int,
    help="Temperature in Kelvin for Langevin Middle integrator",
    required=True,
)
parser.add_argument(
    "--friction_coeff_ps",
    type=int,
    help="Friction coefficient in picoseconds^-1 for Langevin Middle integrator",
    required=True,
)
parser.add_argument(
    "--step_size_ps",
    type=float,
    help="Step size in picoseconds for Langevin Middle integrator",
    required=True,
)
parser.add_argument(
    "--checkpoint_steps",
    type=int,
    help="Number of steps between each checkpoint",
    required=True,
)
parser.add_argument(
    "--total_steps",
    type=int,
    help="Total number of steps to run the simulation",
    required=True,
)

# Finally, we're going to run the simulation if this script is run as the main script
if __name__ == "__main__":
    args = parser.parse_args()
    run_simulation(
        args.input_pdb,
        args.force_fields,
        args.nonbonded_cutoff_nm,
        args.temperature_k,
        args.friction_coeff_ps,
        args.step_size_ps,
        args.checkpoint_steps,
        args.total_steps,
    )
