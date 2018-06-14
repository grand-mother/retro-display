# -*- coding: utf-8 -*-
#
#  Copyright (C) 2017 Université Clermont Auvergne, CNRS/IN2P3, LPC
#  Author: Valentin NIESS (niess@in2p3.fr)
#
#  A basic event display for RETRO, based on matplotlib.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>

import sys
sys.path.append("../../lib/python")

import numpy
import matplotlib.pyplot as plt
from grand_tour import Topography, TurtleError


try:
    # Use this style-sheet if available and supported by the current matplotlib
    # version.
    plt.style.use("deps/mplstyle-l3/style/l3.mplstyle")
except:
    pass


class Display:
    """Display manager for RETRO events"""
    def __init__(self):
        self._origin = None
        self._topo = None

    def __call__(self, event):
        """Display an event"""
        if event["origin"] != self._origin:
            # Update the topography handle if required
            latitude, longitude = self._origin = event["origin"]
            self._topo = Topography(latitude=latitude, longitude=longitude,
                path="share/topography", stack_size=121)

        # Parse the tau decay parameters
        _, _, r0, u, _, _ = event["tau_at_decay"]
        r0, u = map(numpy.array, (r0, u))
        r0 *= 1E-03 # m -> km

        # Compute the shower energy
        shower_energy = 0.
        for (pid_, momentum) in event["decay"]:
            aid = abs(pid_)
            if aid in (12, 13, 14, 16):
                continue
            shower_energy += sum(m**2 for m in momentum)**0.5

        # Build the cone parameters
        zcmin, zcmax = 14., 165E-09 * shower_energy + 55.
        r1 = r0 + u * zcmin
        r2 = r0 + u * zcmax

        # Parse the antenna data
        ra = numpy.array(event["antennas"])[:, :3] * 1E-03
        try:
            amp = numpy.array(event["time_peaks"])
        except KeyError:
            amp = None

        # Plot the topography
        x, y, _ = zip(r0, r1)
        xmin = min(ra[:,0].min(), min(x))
        xmax = max(ra[:,0].max(), max(x))
        ymin = min(ra[:,1].min(), min(y))
        ymax = max(ra[:,1].max(), max(y))
        xt = numpy.linspace(xmin, xmax, 101)
        yt = numpy.linspace(ymin, ymax, 101)
        zt = numpy.zeros((len(yt), len(xt)))
        for i, yi in enumerate(yt):
            for j, xj in enumerate(xt):
                try:
                    zt[i, j] = self._topo.ground_altitude(
                        xj * 1E+03, yi * 1E+03) * 1E-03
                except TurtleError:
                    zt[i, j] = 0.
        fig = plt.figure()
        plt.pcolor(xt, yt, zt, cmap="terrain", alpha=0.75)
        plt.colorbar()

        def onclick(event):
            x, y = event.xdata * 1E+03, event.ydata * 1E+03
            z = self._topo.ground_altitude(x, y)
            print "{:9f}, {:.9f}, {:.0f}".format(
                *self._topo.local_to_lla((x, y, z)))
        cid = fig.canvas.mpl_connect("button_press_event", onclick)

        # Plot the decay
        plt.plot(x[0], y[0], "ro")
        plt.plot(x[1], y[1], "r*")
        plt.plot(x, y, "r-")
        x, y, _ = zip(r1, r2)
        plt.plot(x, y, "r--")

        # Plot the antennas
        plt.plot(ra[:, 0], ra[:, 1], "g.")

        plt.axis((xmin, xmax, ymin, ymax))
        plt.xlabel("northing, $x$ (km)")
        plt.ylabel("westing, $y$ (km)")

        # Profile view
        def plot_ray(s0, s1, mrk, clr):
            s = numpy.linspace(s0, s1, 10001)
            zt, zr = numpy.zeros(s.shape), numpy.zeros(s.shape)
            for i, si in enumerate(s):
                xi, yi, zi = r0 + si * u
                zr[i] = zi
                try:
                    zt[i] = self._topo.ground_altitude(
                        xi * 1E+03, yi * 1E+03) * 1E-03
                except TurtleError:
                    zt[i] = zt[i - 1]
            plt.plot(s, zt, "k-")
            plt.plot(s0, zr[0], mrk)
            plt.plot(s, zr, clr)
        fig = plt.figure()
        sa = numpy.dot(ra - r0, u)
        zcmax = min(max(sa) + 5, zcmax)
        plot_ray(0., zcmin, "ro", "r-")
        plot_ray(zcmin, zcmax, "r*", "r--")
        plt.plot(sa, ra[:,2], "g.")

        _, _, zmin, zmax = plt.axis()
        plt.axis((0., zcmax, zmin, zmax))
        plt.xlabel("distance to decay, $s$ (km)")
        plt.ylabel("altitude, $z$ (km)")

        def onclick(event):
            s, z = event.xdata, event.ydata * 1E+03
            x = (r0[0] + s * u[0]) * 1E+03
            y = (r0[1] + s * u[1]) * 1E+03
            print "{:9f}, {:.9f}, {:.0f}".format(
                *self._topo.local_to_lla((x, y, z)))
        cid = fig.canvas.mpl_connect("button_press_event", onclick)

        plt.show()
