# multi-robot-trajectory-planning

This repository contains code for the following two publications:

W. Hönig, J. A. Preiss, T. K. S. Kumar, G. S. Sukhatme, and N. Ayanian. "Trajectory Planning for Quadrotor Swarms", in IEEE Transactions on Robotics (T-RO), Special Issue Aerial Swarm Robotics, vol. 34, no. 4, pp. 856-869, August 2018. 

and

M. Debord, W. Hönig, and N. Ayanian. "Trajectory Planning for Heterogeneous Robot Teams", in Proc. IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS), Madrid, Spain, October 2018.

The continuous planner is identical to the one used in the IROS paper, while the discrete portion is a re-write using libMultiRobotPlanning.

Currently, this version only supports the 2D case, using (E)CBS as discrete planner.

# Installation (from a clean Ubuntu 22.04. build)

```
git clone --recurse-submodules -j8 https://github.com/lukasulc/multi-robot-trajectory-planning
sudo apt-get update
sudo apt-get install libboost-all-dev
// sudo apt-get install -y build-essential # was not necessary 
sudo apt-get install libyaml-cpp-dev  # Standard package on Ubuntu
sudo apt-get install pkg-config  # Helps CMake locate dependencies
sudo apt-get install doxygen doxygen-gui graphviz  # Installs Doxygen and diagram tools
sudo apt-get install liboctomap-dev  # Standard Ubuntu package 
sudo apt-get install python3-matplotlib
```

## Setup


Tested on Ubuntu 18.04.

```
mkdir build
cd build
cmake ..
make
```

```
cd smoothener
make
Open in matlab
go to external/libsvm/matlab
In Matlab: make
```

## Example

### Discrete Planning

#### Ex. 1

After running the setup, run the following from root of the project:
````
./build/libMultiRobotPlanning/ecbs -i examples/ground/test_2_agents.yaml -o examples/ground/output/discreteSchedule.yaml -w 1.1
````
````
python3 libMultiRobotPlanning/example/visualize.py examples/ground/test_2_agents.yaml examples/ground/output/discreteSchedule.yaml
````
If you get: "no examples/ground/output/discreteSchedule.yaml found error" -> create examples/ground/output directory and run both commands again

#### Ex. 2
````
./build/libMultiRobotPlanning/ecbs -i examples/ground/multi/test_Berlin_1_256_Berlin_1_256-random-1_10_agents.yaml -o examples/ground/multi/output/discreteSchedule_test_Berlin_1_256_Berlin_1_256-random-1_10_agents.yaml -w 1.1
````
````
python3 libMultiRobotPlanning/example/visualize.py examples/ground/multi/test_Berlin_1_256_Berlin_1_256-random-1_10_agents.yaml examples/ground/multi/output/discreteSchedule_test_Berlin_1_256_Berlin_1_256-random-1_10_agents.yaml
````

#### Ex. 3
````
./build/libMultiRobotPlanning/ecbs -i examples/ground/warehouse-10-20-10-2-1/random-1_100_agents.yaml -o examples/ground/warehouse-10-20-10-2-1/output/random-1_100_agents.yaml -w 1.1
````
````
python3 libMultiRobotPlanning/example/visualize.py examples/ground/warehouse-10-20-10-2-1/random-1_100_agents.yaml examples/ground/warehouse-10-20-10-2-1/output/random-1_100_agents.yaml --video examples/ground/warehouse-10-20-10-2-1/100_agents.mp4
````
### Map Conversion

```
./build/tools/map2octomap/map2octomap -m examples/ground/test_2_agents.yaml -o examples/ground/map.bt
./build/tools/octomap2openscad/octomap2openscad -i examples/ground/map.bt -o examples/ground/output/map.scad
openscad -o examples/ground/output/map.stl examples/ground/output/map.scad
(open in meshlab and resave as binary)
```

### Continuous Optimization

```
(open matlab)
(run path_config)
(run smoother)
```

### Temporal stretching

```
python3 tools/scaleTrajectories.py examples/ground/output/pps/ examples/ground/types.yaml examples/ground/test_2_agents.yaml
```