import numpy as np
import os
from PIL import Image
import zarr
from tqdm import tqdm
import argparse
from multiprocessing import Pool

parser = argparse.ArgumentParser(description='Convert n5 to knossos')
parser.add_argument('--n5', type=str, help='Path to n5 container')
parser.add_argument('--dset', type=str, help='n5 dset')
parser.add_argument('--png', type=str, help='png stack output dir')
parser.add_argument('--knossos', type=str, help='knossos output dir')
parser.add_argument('--config', type=str, help='knossos config path')
parser.add_argument('--chunk_size', type=int, help='number of z slices in each chunk', default=500, required=False)

def n5_to_png(input_file, dataset, output_dir, chunk_size=500, verbose=False):
    f = zarr.open(input_file, "r")[dataset]
    shape = f.shape
    print("Convert to png...")
    print(f"Volume size: {shape}")

    if not len(shape) == 3:
        raise ValueError("Input dataset needs to be 3 dimensional.")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    stack_dir = output_dir
    if not os.path.exists(stack_dir):
        os.makedirs(stack_dir)

    n_chunks = int(shape[0]/chunk_size)
    if shape[0] % chunk_size != 0:
        n_chunks += 1

    num_workers = n_chunks
    pool = Pool(processes=num_workers) 
    result = []
    for n in range(n_chunks):
        result.append(pool.apply_async(write_chunk, (input_file,dataset,n,chunk_size,
                                                     n_chunks,stack_dir,shape,)))

    for res in result:
        res.get()

    pool.close()
    pool.join()

def verify_image(im_path):
    im = Image.open(im_path)
    im_arr = np.array(im)
    im.close()
    if not im_arr.shape:
        return False
    return True

def write_chunk(input_file, dataset, n, chunk_size, 
                n_chunks, stack_dir, shape):
    f = zarr.open(input_file, "r")[dataset]
    shape = f.shape
    data = np.array(f[n*chunk_size:(n+1)*chunk_size, :,:])
    effective_chunk_size = np.shape(data)[0]
    print(f"Chunk {n+1}/{n_chunks}")
    for z in tqdm(range(effective_chunk_size), position=n):
        write_successful = False
        tries = 0
        z_real = z + effective_chunk_size * n
        im_name = stack_dir + "/" + "0" * (len(str(shape[0])) - len(str(z_real)) + 1) + str(z_real) + ".png" 
        if os.path.exists(im_name):
            continue

        while not write_successful and tries<10:
            arr = data[z, :, :]
            im = Image.fromarray(arr)
            im.save(im_name, compression_level=0)
            write_successful = verify_image(im_name)
            tries += 1

        if not write_successful:
            print("Write failed for z={}".format(z_real))
            im = np.zeros(np.shape(data[z,:,:]), dtype=np.uint16)
            im.save(im_name, compression_level=0)

def png_to_knossos(stack_dir, output_dir, knossos_config):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    config_flag = "-c {}".format(knossos_config)
    cmd = "knossos_cuber -f png {} {} {}".format(config_flag, stack_dir, output_dir)
    os.system(cmd)

if __name__ == "__main__":
    args = parser.parse_args()

    n5_to_png(args.n5,
              args.dset,
              args.png,
              chunk_size=args.chunk_size)

    png_to_knossos(args.png,
                   args.knossos,
                   knossos_config=args.config)
