# flatc --python --gen-object-api monster.fbs

flatc -o $PWD/ctct/ -I $PWD/interfaces/include --python --gen-object-api interfaces/lift_layers/*.fbs