Convert n5 to knossos by converting to png stacks first (supported by cuber) and applying knossos cuber. Ugly but works.

0. Install requirements:
```
pip install -r requirements.txt
```

1. Install knossos cuber:
```
pip3 install https://github.com/knossos-project/knossos_cuber/archive/master.zip
```

2. Modify knossos cuber config by setting 'scaling' and 'boundary' to the n5 resolution and shape respectively. Can be done automatically if n5 meta data is consistent. 

3. Run script
```bash
python n5_to_knossos.py --n5 path_to_n5 --dset dataset_name --png png_stack_output_dir --knossos knossos_output_dir --config cuber_config_file_path
```
