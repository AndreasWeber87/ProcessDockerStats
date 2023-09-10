In the course of my bachelor thesis, "docker stats" was used to record the resources of Docker containers. This application was developed for the processing of the measured values.

The script performs the following steps for the preparation of the Docker statistics:
1. incomplete rows are removed.
2. values are converted to MB or MiB and the labels for the units are removed, leaving the numbers.
3. measurements where the REST API container is idle (= when CPU usage is less than 2%) are removed.
4. two CSV files for CPU and RAM measurements are written for each container.
5. for better overview in each CSV file the individual measurements are written next to each other instead of under each other.
