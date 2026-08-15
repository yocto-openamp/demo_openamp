
typedef struct
{
    // Name of the controlled axis
    char namex[32];
    // [steps (4096 steps = 1 revolution)] Encoder steps
    uint32_t value;
    // [s] Integral gain (I) of the PID controller
    double i_param;
} ModelPidController_t;
