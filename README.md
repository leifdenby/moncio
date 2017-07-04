# MONC configuration generation in Python

This utility aims to simplify defining which output fields
[MONC](https://www.software.ac.uk/who-do-we-work/monc) should save into the
netCDF diagnostics field. This includes operations like calculating means along
a given axis, slicing, coarse-graining and conditional averaging.

The aim is that the utility will *both* create the necessary XML-configuration
file for MONC to get the desired output and will output Fortran90 code necessary
to calculate the fields that must be comminicated to the IO-server. Currently
only the XML-file is produced, eventually once the best choice of MPI
reductions has been identified the Fortran90 part will be implemented.


## Example usage

Example from [example.py](example.py):

```python
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

# the below creates a group for all fields of a given dimension (i.e.
# a field for each of 3d, 2d and 1d fields)
fields = [w, v, wv, w_horizontal_mean, w_prime_horz, w_clb, q_updraft]
monc_configuration = make_config_with_default_groups(fields)

print monc_configuration.render_xml()
```


Output:

```xml
<?xml version="1.0" ?>
<io-configuration>
  <server-configuration>
    <thread_pool number="100"/>
  </server-configuration>
  <group name="1d">
    <member name="w_horizonal_mean"/>
    <member name="q_updraft"/>
  </group>
  <group name="2d">
    <member name="w_cloudbase"/>
  </group>
  <group name="3d">
    <member name="w"/>
    <member name="v"/>
    <member name="w * v"/>
    <member name="w_prime_horz"/>
  </group>
  <data-writing>
    <file filename="diagnostics.nc" title="default_title" write_time_frequency="100.000000"/>
  </data-writing>
</io-configuration>
```
