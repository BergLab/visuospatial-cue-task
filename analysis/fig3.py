"""Figure 3 - Off-cue stimulation has no significant effect on performance.

Generated panels (A and E are trial schematics):
    B  fig3B_stage8_laser_off_raster.svg   trial outcomes, Stage 8 (stimulation before cue), laser off
    C  fig3C_stage8_laser_on_raster.svg    trial outcomes, Stage 8, laser on
    D  fig3D_stage8_accuracy.svg           accuracy per rat, laser off vs on, Stage 8
    F  fig3F_stage9_laser_off_raster.svg   trial outcomes, Stage 9 (stimulation after cue), laser off
    G  fig3G_stage9_laser_on_raster.svg    trial outcomes, Stage 9, laser on
    H  fig3H_stage9_accuracy.svg           accuracy per rat, laser off vs on, Stage 9
"""
from common import load_sessions, stage_data, raster_matrix, plot_raster, plot_accuracy, savefig

result = load_sessions(verbose=True)

for stage, (p_off, p_on, p_acc) in {8: ("B", "C", "D"), 9: ("F", "G", "H")}.items():
    d = stage_data(result, stage)
    savefig(plot_raster(raster_matrix(d, False), f"Stage {stage}: Laser off"),
            f"fig3{p_off}_stage{stage}_laser_off_raster.svg")
    savefig(plot_raster(raster_matrix(d, True), f"Stage {stage}: Laser on"),
            f"fig3{p_on}_stage{stage}_laser_on_raster.svg")
    savefig(plot_accuracy(d, stage), f"fig3{p_acc}_stage{stage}_accuracy.svg")
