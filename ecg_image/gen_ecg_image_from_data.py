import argparse
import csv
import json
import os
import random
import sys
import warnings

from extract_leads import get_paper_ecg
from helper_functions import read_config_file
from scipy.stats import bernoulli

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
warnings.filterwarnings("ignore")


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", type=str, required=True)
    parser.add_argument("-hea", "--header_file", type=str, required=True)
    parser.add_argument("-o", "--output_directory", type=str, required=True)
    parser.add_argument("-se", "--seed", type=int, required=False, default=-1)
    parser.add_argument("-st", "--start_index", type=int, required=True, default=-1)
    parser.add_argument("--num_leads", type=str, default="twelve")
    parser.add_argument("--config_file", type=str, default="config.yaml")
    parser.add_argument("-r", "--resolution", type=int, required=False, default=200)
    parser.add_argument("--pad_inches", type=int, required=False, default=0)
    parser.add_argument("-ph", "--print_header", action="store_true", default=False)
    parser.add_argument("--num_columns", type=int, default=-1)
    parser.add_argument("--full_mode", nargs="*", type=str, default="None")
    parser.add_argument("--mask_unplotted_samples", action="store_true", default=False)
    parser.add_argument("--add_qr_code", action="store_true", default=False)
    parser.add_argument("-l", "--link", type=str, required=False, default="")
    parser.add_argument("-n", "--num_words", type=int, required=False, default=5)
    parser.add_argument("--x_offset", dest="x_offset", type=int, default=30)
    parser.add_argument("--y_offset", dest="y_offset", type=int, default=30)
    parser.add_argument(
        "--hws", dest="handwriting_size_factor", type=float, default=0.2
    )
    parser.add_argument("-ca", "--crease_angle", type=int, default=90)
    parser.add_argument("-nv", "--num_creases_vertically", type=int, default=10)
    parser.add_argument("-nh", "--num_creases_horizontally", type=int, default=10)
    parser.add_argument("-rot", "--rotate", type=int, default=0)
    parser.add_argument("-noise", "--noise", type=int, default=50)
    parser.add_argument("-c", "--crop", type=float, default=0.01)
    parser.add_argument("-t", "--temperature", type=int, default=40000)
    parser.add_argument("--random_resolution", action="store_true", default=False)
    parser.add_argument("--random_padding", action="store_true", default=False)
    parser.add_argument("--random_grid_color", action="store_true", default=False)
    parser.add_argument("--standard_grid_color", type=int, default=5)
    parser.add_argument("--calibration_pulse", type=float, default=1)
    parser.add_argument("--random_grid_present", type=float, default=1)
    parser.add_argument("--random_print_header", type=float, default=0)
    parser.add_argument("--random_bw", type=float, default=0)
    parser.add_argument("--remove_lead_names", action="store_false", default=True)
    parser.add_argument("--lead_name_bbox", action="store_true", default=False)
    parser.add_argument("--store_config", type=int, nargs="?", const=1, default=0)
    parser.add_argument("--lead_bbox", action="store_true", default=False)
    return parser


def writeCSV(args):
    csv_file_path = os.path.join(args.output_directory, "Coordinates.csv")
    if os.path.isfile(csv_file_path) == False:
        with open(csv_file_path, "a") as ground_truth_file:
            writer = csv.writer(ground_truth_file)
            if args.start_index != -1:
                writer.writerow(
                    ["Filename", "class", "x_center", "y_center", "width", "height"]
                )
    grid_file_path = os.path.join(args.output_directory, "gridsizes.csv")
    if os.path.isfile(grid_file_path) == False:
        with open(grid_file_path, "a") as gridsize_file:
            writer = csv.writer(gridsize_file)
            if args.start_index != -1:
                writer.writerow(
                    ["filename", "xgrid", "ygrid", "lead_name", "start", "end"]
                )


def run_single_file(args):
    if hasattr(args, "st") == True:
        random.seed(args.seed)
        args.encoding = args.input_file
    filename = args.input_file
    header = args.header_file
    resolution = (
        random.choice(range(50, args.resolution + 1))
        if (args.random_resolution)
        else args.resolution
    )
    padding = (
        random.choice(range(0, args.pad_inches + 1))
        if (args.random_padding)
        else args.pad_inches
    )
    papersize = ""
    lead = args.remove_lead_names
    bernoulli_dc = bernoulli(args.calibration_pulse)
    bernoulli_bw = bernoulli(args.random_bw)
    bernoulli_grid = bernoulli(args.random_grid_present)
    if args.print_header:
        bernoulli_add_print = bernoulli(1)
    else:
        bernoulli_add_print = bernoulli(args.random_print_header)
    font = os.path.join("Fonts", random.choice(os.listdir("Fonts")))
    if args.random_bw == 0:
        if args.random_grid_color == False:
            standard_colours = args.standard_grid_color
        else:
            standard_colours = -1
    else:
        standard_colours = False
    configs = read_config_file(os.path.join(os.getcwd(), args.config_file))
    out_array = get_paper_ecg(
        input_file=filename,
        header_file=header,
        configs=configs,
        mask_unplotted_samples=args.mask_unplotted_samples,
        start_index=args.start_index,
        store_configs=args.store_config,
        store_text_bbox=args.lead_name_bbox,
        output_directory=args.output_directory,
        resolution=resolution,
        papersize=papersize,
        add_lead_names=lead,
        add_dc_pulse=bernoulli_dc,
        add_bw=bernoulli_bw,
        show_grid=bernoulli_grid,
        add_print=bernoulli_add_print,
        pad_inches=padding,
        font_type=font,
        standard_colours=standard_colours,
        full_mode=args.full_mode,
        bbox=args.lead_bbox,
        columns=args.num_columns,
        seed=args.seed,
    )
    for out in out_array:
        if args.store_config:
            rec_tail, extn = os.path.splitext(out)
            with open(rec_tail + ".json", "r") as file:
                json_dict = json.load(file)
        else:
            json_dict = None

        num_words = 0
        x_offset = 0
        y_offset = 0
        if args.store_config == 2:
            json_dict["handwritten_text"] = bool(hw_text)
            json_dict["num_words"] = num_words
            json_dict["x_offset_for_handwritten_text"] = x_offset
            json_dict["y_offset_for_handwritten_text"] = y_offset

        crease_angle = 0
        num_creases_horizontally = 0
        num_creases_vertically = 0
        if args.store_config == 2:
            json_dict["wrinkles"] = False
            json_dict["crease_angle"] = crease_angle
            json_dict["number_of_creases_horizontally"] = num_creases_horizontally
            json_dict["number_of_creases_vertically"] = num_creases_vertically

        crop = 0
        temp = 0
        rotate = 0
        noise = 0
        if args.store_config == 2:
            json_dict["augment"] = False
            json_dict["crop"] = crop
            json_dict["temperature"] = temp
            json_dict["rotate"] = rotate
            json_dict["noise"] = noise
        if args.store_config:
            json_object = json.dumps(json_dict, indent=4)
            with open(rec_tail + ".json", "w") as f:
                f.write(json_object)

    return len(out_array)


if __name__ == "__main__":
    path = os.path.join(os.getcwd(), sys.argv[0])
    parentPath = os.path.dirname(path)
    os.chdir(parentPath)
    run_single_file(get_parser().parse_args(sys.argv[1:]))
