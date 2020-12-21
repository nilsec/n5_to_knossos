import numpy as np
import os
from PIL import Image
import zarr
import time
from tqdm import tqdm
import argparse

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
    for n in range(n_chunks):
        data = np.array(f[n*chunk_size:(n+1)*chunk_size, :,:])
        effective_chunk_size = np.shape(data)[0]
        print(f"Chunk {n+1}/{n_chunks}")
        for z in tqdm(range(effective_chunk_size)):
            start = time.time()
            arr = data[z, :, :]
            if verbose:
                print("Array conversion takes {} s".format(time.time() - start))
            start = time.time()
            im = Image.fromarray(arr)
            if verbose:
                print("Fromarray takes {} s".format(time.time() - start))

            start = time.time()
            z_real = z + effective_chunk_size * n
            im_name = stack_dir + "/" + "0" * (len(str(shape[0])) - len(str(z_real)) + 1) + str(z_real) + ".png" 
            if os.path.exists(im_name):
                if verbose:
                    print("Skip image")
                continue
            im.save(im_name, compression_level=0)
            if verbose:
                print("Saving image takes {} s".format(time.time() - start))

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
