"""Figure 2 - Performance is obstructed when PTg stimulation occurs during cue presentation.

Generated panels (A-D are schematics and photographs):
    E  fig2E_stage6_laser_off_raster.svg    trial outcomes, Stage 6, laser-off trials
    F  fig2F_stage6_laser_on_raster.svg     trial outcomes, Stage 6, laser-on trials
    G  fig2G_stage6_accuracy.svg            accuracy per rat, laser off vs on, Stage 6
    H  fig2H_stage6_laser_off_simulated.svg panel E with simulated random outcomes (p = 1/3)
    I  fig2I_stage6_laser_on_simulated.svg  panel F with simulated random outcomes (p = 1/3)
    J  fig2J_stage7_accuracy.svg            accuracy per rat, laser off vs on, Stage 7
"""
import numpy as np

from common import load_sessions, stage_data, raster_matrix, simulate_random, plot_raster, plot_accuracy, savefig

SIMULATION_SEED = 0

result = load_sessions(verbose=True)
s6 = stage_data(result, 6)
rng = np.random.default_rng(SIMULATION_SEED)

for laser_on, (real_panel, sim_panel), tag in [(False, ("E", "H"), "off"), (True, ("F", "I"), "on")]:
    m = raster_matrix(s6, laser_on)
    savefig(plot_raster(m, f"Stage 6: Laser {tag}"), f"fig2{real_panel}_stage6_laser_{tag}_raster.svg")
    sim = simulate_random(m, rng)
    print(f"Simulated laser-{tag} accuracy: {(sim == 1).sum() / ((sim == 1) | (sim == 2)).sum():.3f}")
    savefig(plot_raster(sim, "Simulated random responses"), f"fig2{sim_panel}_stage6_laser_{tag}_simulated.svg")

savefig(plot_accuracy(s6, 6), "fig2G_stage6_accuracy.svg")
savefig(plot_accuracy(stage_data(result, 7), 7), "fig2J_stage7_accuracy.svg")
