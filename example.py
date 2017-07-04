from moncio import Field, make_config_with_default_groups
# define starting fields

w = Field('w')
v = Field('v')
q = Field('q')

# sum, product and difference all works as expected (this checks the shape
# hasn't been modified through say coarse-graining)
wv = w*v

# example of creating a horizontal mean
w_horizontal_mean = w.mean(axis=0).mean(axis=1)
w_horizontal_mean.name = "w_horizonal_mean"

# to calculate deviations from the mean the mean profile must be repeated
# along the axis along which the mean was calculated
w_prime_horz = w_horizontal_mean.repeat(axis=1).repeat(axis=0) - w
w_prime_horz.name = "w_prime_horz"

# example of slicing at given z-index
w_clb = w[:,:,12]
w_clb.name = "w_cloudbase"

# example of conditional averaging
updraft_mask = w > 0.0
q_updraft = q.mean(axis=0, mask=updraft_mask).mean(axis=1, mask=updraft_mask)
q_updraft.name = "q_updraft"

# coarse-graining, every "level" merges neighbours, so that with level=3 the
# patches will have 2**3=8, 8x8x8 cells
q_coarse = q.coarsen(level=1)
q_coarse.name = "q_coarse"

# the below creates a group for all fields of a given dimension (i.e.
# a field for each of 3d, 2d and 1d fields)
fields = [w, v, wv, w_horizontal_mean, w_prime_horz, w_clb, q_updraft, q_coarse]
monc_configuration = make_config_with_default_groups(fields)

print monc_configuration.render_xml()
