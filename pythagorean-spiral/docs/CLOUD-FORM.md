# The cloud, in four arcs

Start simple: four clothoid-like arcs, two big ones under the cloud and two half-size ones on top, meeting at the centre and at the top. The first plot is exactly as stated; the second is the smallest change that makes the arcs meet.

```text
bottom centres  (120,120) and (-120,120)
bottom meet     (0,0), radius 169.71
top centres     (60,180) and (-60,180)
top meet        (0,200), radius 63.25
top / bottom    0.37 of the size
```


## 1. As stated

![The four circles, their centres, and the two stated meeting points.](fig/cloud-form-stated.svg)

*The four circles, their centres, and the two stated meeting points.*

The stated form does not close. The bottom pair meets at (0,0) and again at (0,240); the top pair meets at both (0,200) and (0,160); but the bottom-right circle and the top-right circle are nested, not crossing: the centres are 84.85 apart, the radii are 169.71 and 63.25, and the small circle sits 21.61 inside the big one. So the side meeting point does not exist yet.

```text
centre distance   84.85
radii             169.71 + 63.25
needed for a meet r_bottom <= 148.10
current gap       21.61
```

Two easy fixes: shrink the bottom radius below 148.10, or move the bottom centres inward. Shrinking the radius changes the lobe's size; moving the centres changes where the lobe sits. The second is closer to the sketch, so it is the one plotted below.


## 2. Adjusted to meet

![The bottom centres pulled in to (100,100); the arcs now cross, and the outer crossing becomes the side meeting point.](fig/cloud-form-adjusted.svg)

*The bottom centres pulled in to (100,100); the arcs now cross, and the outer crossing becomes the side meeting point.*

With the bottom centres at (100,100) the radius is 141.42 -- and that is also the distance from either centre to (0,200). So the bottom pair now passes through both (0,0) **and** (0,200), and the top pair already passes through (0,200). That is the common point: all four arcs meet there, and the cloud closes at the top centre. The circles also cross again at (80.0, 240.0) on the right; that side crossing is not needed once the arcs are trimmed at the common point.

Two numbers are still off. The big lobes reach x = 241, so the cloud is about 480 wide, roughly twice the intended 200; and the tangent at (0,200) is not continuous -- the bottom arc arrives steep and the top arc leaves shallow, which is G0, not G1. The next tune is therefore one centre and one tangent: bring the bottom centres in to shrink the width, then rotate the top arc about the common point until the tangents agree.


## Reproduce

```text
cd pythagorean-spiral
../.venv/bin/python scripts/cloud_form.py
```
