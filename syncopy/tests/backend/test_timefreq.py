import numpy as np
import matplotlib.pyplot as ppl

from syncopy.specest import mtmfft
from syncopy.specest import superlet, wavelet
from syncopy.specest import wavelets as spywave


def gen_testdata(freqs=[20, 40, 60],
                 cycles=11, fs=1000,
                 eps = 0):

    '''
    Harmonic superposition of multiple
    few-cycle oscillations akin to the
    example of Figure 3 in Moca et al. 2021 NatComm

    Each harmonic has a frequency neighbor with +10Hz
    and a time neighbor after 2 cycles(periods).
    '''

    signal = []
    for freq in freqs:
        
        # 10 cycles of f1
        tvec = np.arange(cycles / freq, step=1 / fs)

        harmonic = np.cos(2 * np.pi * freq * tvec)
        # frequency neighbor
        f_neighbor = np.cos(2 * np.pi * (freq + 10) * tvec) 
        packet = harmonic +  f_neighbor

        # 2 cycles time neighbor
        delta_t = np.zeros(int(2 / freq * fs))
        
        # 5 cycles break
        pad = np.zeros(int(5 / freq * fs))

        signal.extend([pad, packet, delta_t, harmonic])

    # stack the packets together with some padding        
    signal.append(pad)
    signal = np.concatenate(signal)

    # additive white noise
    if eps > 0:
        signal = np.random.randn(len(signal)) * eps + signal
    
    return signal


fs = 1000 # sampling frequency

# generate 3 packets at 20, 40 and 60Hz with 10 cycles each
# Noise variance is given by eps
signal_freqs = np.array([20, 40, 60])
cycles = 10
A = 100 # signal amplitude
signal = A * gen_testdata(freqs=signal_freqs, cycles=cycles, fs=fs, eps=0.) 

# define frequencies of interest for time-frequency methods
foi = np.arange(1, 101, step=1)

# closest spectral indices to validate time-freq results
freq_idx = []
for frequency in signal_freqs:
    freq_idx.append(np.argmax(foi >= frequency))
    
    
def test_superlet():
    
    scalesSL = superlet.scale_from_period(1 / foi)
    spec = superlet.superlet(signal,
                             samplerate=fs,
                             scales=scalesSL,
                             order_max=30,
                             order_min=5,
                             c_1=3,
                             adaptive=True)
    # amplitude spectrum
    ampls = np.abs(spec)

    fig, (ax1, ax2) = ppl.subplots(2, 1,
                                   sharex=True,
                                   gridspec_kw={"height_ratios": [1, 3]},
                                   figsize=(6, 6))
    
    ax1.set_title("Superlet Transform")        
    ax1.plot(np.arange(signal.size) / fs, signal, c='cornflowerblue')
    ax1.set_ylabel('signal (a.u.)')
    
    ax2.set_xlabel("time (s)")    
    ax2.set_ylabel("frequency (Hz)")        
    extent = [0, len(signal) / fs, foi[0], foi[-1]]
    # test also the plotting
    # scale with amplitude
    assert ax2.imshow(ampls,
                      cmap='magma',
                      aspect='auto',
                      extent=extent,
                      origin='lower',
                      vmin=0,
                      vmax=1.2 * A)
    
    # get the 'mappable'
    im = ax2.images[0]
    fig.colorbar(im, ax = ax2, orientation='horizontal',
                 shrink=0.7, pad=0.2, label='amplitude (a.u.)')

    for idx, frequency in zip(freq_idx, signal_freqs):

        ax2.plot([0, len(signal) / fs],
                 [frequency, frequency],
                 '--',
                 c='0.5')

        # number of cycles with relevant
        # amplitude at the respective frequency
        cycle_num = (ampls[idx, :] > A / np.e).sum() / fs * frequency
        # print(f'{cycle_num} cycles for the {frequency} band')
        # we have 2 times the cycles for each frequency (temporal neighbor)
        assert cycle_num > 2 * cycles
        # power should decay fast, so we don't detect more cycles
        assert cycle_num < 3 * cycles

    fig.tight_layout()

    
def test_wavelet():

    # get a wavelet function
    wfun = spywave.Morlet(10)
    scales = wfun.scale_from_period(1 / foi)

    spec = wavelet.wavelet(signal,
                           samplerate=fs,
                           scales=scales,
                           wavelet=wfun)
    # amplitude spectrum
    ampls = np.abs(spec)

    fig, (ax1, ax2) = ppl.subplots(2, 1,
                                   sharex=True,
                                   gridspec_kw={"height_ratios": [1, 3]},
                                   figsize=(6, 6))
    ax1.set_title("Wavelet Transform")
    ax1.plot(np.arange(signal.size) / fs, signal, c='cornflowerblue')
    ax1.set_ylabel('signal (a.u.)')
    
    ax2.set_xlabel("time (s)")    
    ax2.set_ylabel("frequency (Hz)")
    extent = [0, len(signal) / fs, foi[0], foi[-1]]

    # test also the plotting
    # scale with amplitude
    assert ax2.imshow(ampls,
                      cmap='magma',
                      aspect='auto',
                      extent=extent,
                      origin='lower',
                      vmin=0,
                      vmax=1.2 * A)

    # get the 'mappable'
    im = ax2.images[0]
    fig.colorbar(im, ax = ax2, orientation='horizontal',
                 shrink=0.7, pad=0.2, label='amplitude (a.u.)')

    for idx, frequency in zip(freq_idx, signal_freqs):

        ax2.plot([0, len(signal) / fs],
                 [frequency, frequency],
                 '--',
                 c='0.5')

        # number of cycles with relevant
        # amplitude at the respective frequency
        cycle_num = (ampls[idx, :] > A / np.e).sum() / fs * frequency
        print(f'{cycle_num} cycles for the {frequency} band')
        # we have at least 2 times the cycles for each frequency (temporal neighbor)
        assert cycle_num > 2 * cycles
        # power should decay fast, so we don't detect more cycles
        assert cycle_num < 3 * cycles

    fig.tight_layout()

    
def test_mtmfft():

    # superposition 40Hz and 100Hz oscillations 3:2 for 1s
    f1, f2 = 40, 100
    A1, A2 = 3, 2
    tvec = np.arange(0, 1, 1 / 1000)

    signal = A1 * np.cos(2 * np.pi * 40 * tvec)
    signal += A2 * np.cos(2 * np.pi * 100 * tvec)

    # test untapered
    taperopt = {}
    ftr, freqs = mtmfft.mtmfft(signal, fs, taper=None)

    # with 1000Hz sampling frequency and 1000 samples this gives
    # exactly 1Hz frequency resolution ranging from 0 - 500Hz:
    assert freqs[f1] == f1
    assert freqs[f2] == f2

    # average over potential tapers (only 1 here)
    spec = np.real(ftr * ftr.conj()).mean(axis=0)
    amplitudes = np.sqrt(spec)[:, 0] # only 1 channel

    fig, ax = ppl.subplots()
    ax.set_title("Amplitude spectrum 3 x 40Hz + 2 x 100Hz")
    ax.plot(freqs[:150], amplitudes[:150], label="No taper", lw=2)
    ax.set_xlabel('frequency (Hz)')
    ax.set_ylabel('amplitude (a.u.)')

    # our FFT normalisation recovers the signal amplitudes:
    assert np.allclose([A1, A2], amplitudes[[f1, f2]]) 

    # test hann taper
    ftr, freqs = mtmfft.mtmfft(signal, fs, taper="hann")
    # average over tapers (only 1 here)
    hann_spec = np.real(ftr * ftr.conj()).mean(axis=0)
    hann_amplitudes = np.sqrt(hann_spec)[:, 0] # only 1 channel

    # check for amplitudes (and taper normalisation)
    assert np.allclose([A1, A2], hann_amplitudes[[f1, f2]], rtol=1e-2)

    # test kaiser taper (is the box for beta -> inf)
    taperopt = {'beta' : 2}
    ftr, freqs = mtmfft.mtmfft(signal, fs, taper="kaiser", taperopt=taperopt)
    # average over tapers (only 1 here)
    kaiser_spec = np.real(ftr * ftr.conj()).mean(axis=0)
    kaiser_amplitudes = np.sqrt(kaiser_spec)[:, 0] # only 1 channel

    # Kaiser taper is not normalised :/, check at least the ratio
    assert np.allclose(A1 / A2, kaiser_amplitudes[f1] / kaiser_amplitudes[f2], rtol=1e-4) 

    # test multi-taper analysis 
    taperopt = {'Kmax' : 6, 'NW' : 1}
    ftr, freqs = mtmfft.mtmfft(signal, fs, taper="dpss", taperopt=taperopt)
    # average over tapers 
    dpss_spec = np.real(ftr * ftr.conj()).mean(axis=0)
    dpss_amplitudes = np.sqrt(dpss_spec)[:, 0] # only 1 channel
    ax.plot(freqs[:150], dpss_amplitudes[:150], label="Slepian", lw=2)
    ax.legend()

    # Slepian tapers are normalized
    assert np.allclose([A1, A2], dpss_amplitudes[[f1, f2]], rtol=1e-2) 
