# OpenMM

This repo builds a docker image with OpenMM and CUDA, using miniconda.
See [available tags.](https://hub.docker.com/r/saladtechnologies/openmm/tags)

## Example Usage

See the [example dockerfile](./Dockerfile.example) for a simple example of how to run custom simulations based on this image.

### Example Kelpie Job

Once you've got your docker image built, and deployed to a Salad Container Group, you can run a simulation by submitting a job to the Kelpie API. This assumes your bucket is already set up and named `my-simulation-bucket`. Adjust all the paths and arguments as needed.

**POST https://kelpie.saladexamples.com/jobs**
Header: `Kelpie-Api-Key: <your-api-key>`
```json
{
  "command": "python",
  "arguments": [
    "/workspaces/openmm/simulation.py",
    "--input_pdb", "input.pdb",
    "--force_fields", "amber14-all.xml", "amber14/tip3pfb.xml",
    "--nonbonded_cutoff_nm", "1",
    "--temperature_k", "300",
    "--friction_coeff_ps", "1",
    "--step_size_ps", "0.004",
    "--checkpoint_steps", "1000",
    "--total_steps", "10000"
  ],
  "sync": {
    "before": [
      {
        "bucket": "my-simulation-bucket",
        "prefix": "some-job-id/",
        "local_path": "/workspaces/openmm/",
        "direction": "download"
      }
    ],
    "during" : [
      {
        "bucket": "my-simulation-bucket",
        "prefix": "some-job-id/",
        "local_path": "/workspaces/openmm/",
        "direction": "upload",
        "pattern": "checkpoint\\.chk"
      }
    ],
    "after": [
      {
        "bucket": "my-simulation-bucket",
        "prefix": "some-job-id/",
        "local_path": "/workspaces/openmm/",
        "direction": "upload",
        "pattern": "final_state\\.pdb"
      }
    ]
  },
  "container_group_id": "aa283fda-94f6-4a01-a47b-ca9ef01ebc0f",
}
```