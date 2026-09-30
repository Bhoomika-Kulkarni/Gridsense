from common import (
    load_config,
    initialize_random_seed,
    create_output_directories,
    get_regions,
)


def main():
    config = load_config()

    initialize_random_seed(config)
    create_output_directories(config)

    print("GridSense configuration loaded successfully.")
    print("Project:", config["project"]["name"])
    print("Regions:", get_regions(config))
    print("Random seed:", config["project"]["random_seed"])
    print("Customer count:", config["record_counts"]["customers"])
    print("Meter count:", config["record_counts"]["meters"])


if __name__ == "__main__":
    main()