#!/bin/bash

# Run simulation participants
# Run Fluid participant
./Fluid_participant &
# Run Solid participant
./Solid_participant &

# Wait for all participants to complete
wait
