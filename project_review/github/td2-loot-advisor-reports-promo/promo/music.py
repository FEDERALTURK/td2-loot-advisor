"""Özgün arka plan müziği (tamamen sentez, hiçbir kayıt/örnek kullanılmaz): karanlık, gerilimli taktik ambiyans.
    python music.py <süre_sn> <çıktı.wav>
92 BPM; A minör: Am - F - C - G; alt bas nabzı, yumuşak pad, metalik tik sesleri, açılışta yükselen dalga, sonda vuruş.
"""
import sys, wave
import numpy as np

DUR = float(sys.argv[1]); OUT = sys.argv[2]
SR = 48000
n = int(DUR * SR); t = np.arange(n) / SR
rng = np.random.default_rng(7)
BPM = 92; beat = 60 / BPM; bar = 4 * beat


def note(m): return 440.0 * 2 ** ((m - 69) / 12)


def env_ad(length, a, d):
    e = np.ones(length)
    ai = min(int(a * SR), length // 2); di = min(int(d * SR), length - ai)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if di: e[-di:] *= np.linspace(1, 0, di)
    return e


chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]       # Am F C G (MIDI)
L = np.zeros(n); R = np.zeros(n)
# pad: detuned saws softened (additive, few harmonics) per bar
nbars = int(np.ceil(DUR / bar))
for b in range(nbars):
    s0 = int(b * bar * SR); s1 = min(n, int((b + 1) * bar * SR) + int(0.4 * SR))
    if s0 >= n: break
    tt = np.arange(s1 - s0) / SR
    e = env_ad(s1 - s0, 0.8, 0.9)
    for m in chords[b % 4]:
        for det, pan in ((-0.12, 0.3), (0.12, 0.7)):
            f = note(m) * 2 ** (det / 12)
            w = sum(np.sin(2 * np.pi * f * k * tt + k) / k ** 1.6 for k in range(1, 6))
            L[s0:s1] += 0.035 * e * w * (1 - pan); R[s0:s1] += 0.035 * e * w * pan
    # sub bass pulse on 8ths
    root = chords[b % 4][0] - 24
    for k in range(8):
        p0 = s0 + int(k * beat / 2 * SR); ln = int(0.22 * SR)
        if p0 + ln > n: break
        tt2 = np.arange(ln) / SR
        w = np.sin(2 * np.pi * note(root) * tt2) * np.exp(-tt2 * 11)
        acc = 1.0 if k % 2 == 0 else 0.55
        L[p0:p0 + ln] += 0.16 * acc * w; R[p0:p0 + ln] += 0.16 * acc * w
# ticks (filtered noise) on 16ths after intro, soft kick on beats
start_perc = 2 * bar
for i in range(int(DUR / (beat / 4))):
    p0 = int(i * beat / 4 * SR)
    if p0 / SR < start_perc or p0 + 2400 > n: continue
    ln = 2400; nz = rng.standard_normal(ln) * np.exp(-np.arange(ln) / SR * 90)
    nz = np.diff(np.concatenate([[0], nz]))                                    # tiz
    v = 0.05 if i % 4 == 2 else 0.022
    pan = 0.35 if i % 2 else 0.65
    L[p0:p0 + ln] += v * nz * (1 - pan); R[p0:p0 + ln] += v * nz * pan
for i in range(int(DUR / beat)):
    p0 = int(i * beat * SR)
    if p0 / SR < start_perc or p0 + 9000 > n: continue
    tt3 = np.arange(9000) / SR
    k = np.sin(2 * np.pi * (48 + 90 * np.exp(-tt3 * 30)) * tt3) * np.exp(-tt3 * 14)
    L[p0:p0 + 9000] += 0.22 * k; R[p0:p0 + 9000] += 0.22 * k
# rising swell into the first downbeat
sw = int(2 * bar * SR)
nz = rng.standard_normal(sw)
nz = np.convolve(nz, np.ones(40) / 40, mode="same")
ramp = np.linspace(0, 1, sw) ** 2.5
L[:sw] += 0.12 * nz * ramp; R[:sw] += 0.12 * np.roll(nz, 300) * ramp
# final hit + tail
hit = int((DUR - 3.2) * SR)
if hit > 0:
    ln = n - hit; tt4 = np.arange(ln) / SR
    boom = np.sin(2 * np.pi * 41 * tt4) * np.exp(-tt4 * 1.6) + 0.4 * rng.standard_normal(ln) * np.exp(-tt4 * 9)
    L[hit:] += 0.32 * boom; R[hit:] += 0.32 * boom
# simple stereo reverb (comb)
for d, g in ((0.031, 0.35), (0.047, 0.3), (0.089, 0.22)):
    k = int(d * SR)
    L[k:] += g * R[:-k] * 0.5; R[k:] += g * L[:-k] * 0.5
fade = env_ad(n, 0.05, 1.2)
L *= fade; R *= fade
mx = max(np.abs(L).max(), np.abs(R).max()); L /= mx * 1.12; R /= mx * 1.12
pcm = (np.stack([L, R], 1) * 32767).astype("<i2")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("music", OUT, DUR)

