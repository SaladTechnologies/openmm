# OpenMM

This repo builds a docker image with OpenMM and CUDA, using miniconda.
See [available tags.](https://hub.docker.com/r/saladtechnologies/openmm/tags)

**Run it Locally**

```bash
docker run --gpus all --rm -it saladtechnologies/openmm:cuda11.8
```

You should see something like this:

```
OpenMM Version: 8.1.1
Git Revision: ec797acabe5de4ce9f56c92d349baa889f4b0821

There are 3 Platforms available:

1 Reference - Successfully computed forces
2 CPU - Successfully computed forces
3 CUDA - Successfully computed forces

Median difference in forces between platforms:

Reference vs. CPU: 6.2966e-06
Reference vs. CUDA: 6.7376e-06
CPU vs. CUDA: 7.38656e-07

All differences are within tolerance.
```

## Example Usage

See the [example dockerfile](./Dockerfile.example) for a simple example of how to run custom simulations based on this image.

### Example Kelpie Job

[Kelpie](https://github.com/SaladTechnologies/kelpie) is an open-source job orchestration system that can manage large batches of long-running jobs on Salad's infrastructure.

Once you've got your docker image built, and deployed to a Salad Container Group, you can run a simulation by submitting a job to the Kelpie API. This assumes your bucket is already set up and named `my-simulation-bucket`. Adjust all the paths and arguments as needed.

**POST https://kelpie.saladexamples.com/jobs**

Header: `Kelpie-Api-Key: <your-api-key>`
```json
{
  "command": "python",
  "arguments": [
    "/workspaces/openmm/simulation.py",
    "--input_pdb", "/workspaces/openmm/sim-data/input.pdb",
    "--force_fields", "amber14-all.xml", "amber14/tip3pfb.xml",
    "--nonbonded_cutoff_nm", "1",
    "--temperature_k", "300",
    "--friction_coeff_ps", "1",
    "--step_size_ps", "0.004",
    "--checkpoint_steps", "10000",
    "--total_steps", "100000"
  ],
  "sync": {
    "before": [
      {
        "bucket": "my-simulation-bucket",
        "prefix": "round-1/some-job-id/",
        "local_path": "/workspaces/openmm/sim-data/",
        "direction": "download"
      }
    ],
    "during" : [
      {
        "bucket": "my-simulation-bucket",
        "prefix": "round-1/some-job-id/",
        "local_path": "/workspaces/openmm/sim-data/",
        "direction": "upload",
        "pattern": "checkpoint\\.chk"
      }
    ],
    "after": [
      {
        "bucket": "my-simulation-bucket",
        "prefix": "round-1/some-job-id/",
        "local_path": "/workspaces/openmm/sim-data/",
        "direction": "upload",
        "pattern": "final_state\\.pdb"
      }
    ]
  },
  "container_group_id": "your-container-group-id",
}
```

Let's go over the parts of this payload, and how they map to our simulation script.

- `command` and `arguments` are the command and arguments to run in the container. In this case, we're running a Python script at `/workspaces/openmm/simulation.py`, and passing in a bunch of arguments. This is the equivalent of running the following bash command in your terminal:
  
  ```bash
  python /workspaces/openmm/simulation.py \
  --input_pdb /workspaces/openmm/sim-data/input.pdb \
  --force_fields amber14-all.xml amber14/tip3pfb.xml \
  --nonbonded_cutoff_nm 1 \
  --temperature_k 300 \
  --friction_coeff_ps 1 \
  --step_size_ps 0.004 \
  --checkpoint_steps 10000 \
  --total_steps 100000
  ```

  In our simulation script, we've used the `argparse` library to parse these arguments. You can see how we've done this in the [example simulation script](./simulation.py#L75-L120).

- `sync` is an object that tells Kelpie what files to sync to and from the container. In this case, we're downloading the `input.pdb` file from the bucket before the job starts, and uploading the `checkpoint.chk` and `final_state.pdb` files to the bucket during and after the job, respectively.
  - `sync.before` is a list of objects that describe files to download before the job starts. In our case we only need one object to describe what we want to download.
    - `bucket` is the name of the s3-compatible bucket to sync with.
    - `prefix` is the prefix within the bucket where the files are located. You can think of this as a directory or path, and it's often displayed as such in s3-compatible storage systems. In our case, we're downloading files from the `round-1/some-job-id/` directory within the bucket, which will contain the `input.pdb` file, and possibly a `checkpoint.chk` file if the job was restarted.
    - `local_path` is the path within the container where the files should be downloaded to. We define this path here [in the sumulation script](./simulation.py#L10)
    - `direction` is the direction of the sync. In this case, we're downloading files from the bucket, so the direction is `download`. For the `before` sync, this is always `download`.
  - `sync.during` is a list of objects that describe files to sync during the job. In our case we only need one object to describe what we want to upload.
    - `bucket`, `prefix`, and `local_path` are the same as in `sync.before`.
    - `direction` is the same as in `sync.before`, but for the `during` sync, this is always `upload`.
    - `pattern` is an ECMAScript (javascript) regular expression pattern that describes which files to upload. Because the expression is being submitted in a JSON object, special characters must be double-escaped, as in `\\.` for the literal character `.`. In our case, we're uploading any file that matches the pattern `checkpoint.chk`, which is the name of the checkpoint file saved [by the simulation script](./simulation.py#L12) during the job. This is useful for restarting the job from a checkpoint if it fails or the node is interrupted. The pattern field is optional, and if omitted, all files in the `local_path` directory will be uploaded.
  - `sync.after` is a list of objects that describe files to upload after the job finishes. In our case we only need one object to describe what we want to upload.
    - `bucket`, `prefix`, and `local_path` are the same as in `sync.before`.
    - `direction` is the same as in `sync.before`, but for the `after` sync, this is always `upload`.
    - `pattern` is the same as in `sync.during`, but in our case we're uploading the `final_state.pdb` file, which is the final state of the simulation, output by [the simulation script](./simulation.py#L13) This is useful for analysis and visualization of the simulation results.
- `container_group_id` is the ID of the container group to run the job on. For now, this must be retrieved with the Salad API, using the [Get Container Group Endpoint](https://docs.salad.com/api-reference/container_groups/get-a-container-group).

The Kelpie API supports several more options for job submission, including environment variables, webhook notifications, and more. See the [Kelpie API Reference](https://kelpie.saladexamples.com/docs#/default/post_CreateJob) for more information.