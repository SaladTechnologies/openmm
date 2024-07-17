FROM continuumio/miniconda3:23.10.0-1

RUN conda install -c conda-forge openmm cudatoolkit=11.8 -y

CMD ["python", "-m", "openmm.testInstallation"]