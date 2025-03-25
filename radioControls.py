import subprocess
import csv
import time
import os
import threading
from PySide6.QtCore import QThread, Signal

class ScanThread(QThread):
    scan_complete = Signal(list)

    def __init__(self, band_name, start_freq, end_freq, step, integration_time, threshold, output_csv):
        super().__init__()
        self.band_name = band_name
        self.start_freq = start_freq
        self.end_freq = end_freq
        self.step = step
        self.integration_time = integration_time
        self.threshold = threshold
        self.output_csv = output_csv

    def run(self):
        candidates = scan_band(self.band_name, self.start_freq, self.end_freq,
                               self.step, self.integration_time, self.threshold, self.output_csv)
        self.scan_complete.emit(candidates)

    def scan_band(band_name, start_freq, end_freq, step, integration_time, threshold, output_csv):
        """
        Run rtl_power over a frequency range and return a list of candidate frequencies
        where the signal strength exceeds 'threshold' (in dB).
        
        Parameters:
        band_name (str): A label for the band (e.g., "FM")
        start_freq (float): Start frequency in Hz.
        end_freq (float): End frequency in Hz.
        step (float): Step size in Hz.
        integration_time (float): Integration time per measurement (in seconds).
        threshold (float): Minimum power (in dB) to be considered a candidate.
        output_csv (str): The filename for the CSV output.
        
        Returns:
        List of candidate frequencies (floats in Hz), sorted in ascending order.
        """
        # Build the rtl_power command.
        # Example: rtl_power -f 88000000:108000000:200000 -i 0.5 -E 1 -F csv > fm_scan.csv
        cmd = f"rtl_power -f {start_freq}:{end_freq}:{step} -i {integration_time} -1 {output_csv}"
        print("Running command:", cmd)
        subprocess.run(cmd, shell=True)
        # time.sleep(11)
        candidates = []
        if os.path.exists(output_csv):
            with open(output_csv, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    try:
                        freq = float(row[0])
                        power = float(row[1])
                        if power > threshold:
                            candidates.append(freq)
                    except Exception:
                        continue
        candidates.sort()
        print(f"Found {len(candidates)} candidate frequencies in band {band_name}")
        return candidates

    def seek_next(current_freq, candidates):
        """Return the first candidate frequency greater than current_freq; wrap around if needed."""
        for freq in candidates:
            if freq > current_freq:
                return freq
        return candidates[0] if candidates else current_freq

    def seek_previous(current_freq, candidates):
        """Return the last candidate frequency less than current_freq; wrap around if needed."""
        for freq in reversed(candidates):
            if freq < current_freq:
                return freq
        return candidates[-1] if candidates else current_freq

    def parse_rtl_power_csv(filename, threshold=10):
        """
        Reads an rtl_power CSV file and returns a sorted list of candidate frequencies
        that exceed 'threshold' dB.
        
        :param filename: Path to the CSV file generated by rtl_power.
        :param threshold: Minimum dB level to be considered a 'strong' signal.
        :return: A sorted list of candidate frequencies (floats in Hz).
        """
        candidates = []

        with open(filename, 'r', newline='') as csvfile:
            # Many rtl_power outputs are space or tab separated, so we can split on whitespace:
            reader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)

            for row in reader:
                # Skip rows that don't have enough columns
                if len(row) < 7:
                    continue

                try:
                    # Parse the known columns
                    start_freq = float(row[2])   # in Hz
                    end_freq   = float(row[3])   # in Hz
                    bin_size   = float(row[4])   # in Hz
                    # row[5] is FFT size (we won't necessarily need it)
                    
                    # The remaining columns in row[6:] are power values in dB
                    power_values = [float(x) for x in row[6:]]

                    # For each sub-bin i, the frequency is start_freq + i * bin_size
                    for i, pwr in enumerate(power_values):
                        if pwr > threshold:
                            freq_candidate = start_freq + i * bin_size
                            candidates.append(freq_candidate)
                except ValueError:
                    # Could not parse the row properly, skip it
                    continue
                except IndexError:
                    # If something is out of range, skip it
                    continue

        # Remove duplicates (if any) and sort
        unique_candidates = sorted(set(candidates))
        return unique_candidates


    # Example usage:
    def stong_freq(self):
        filename = "/home/marceversole/WorkingPipBoy/fm_scan.csv"
        threshold = 10  # Adjust threshold as needed
        strong_freqs = self.parse_rtl_power_csv(filename, threshold=threshold)
        print(f"Found {len(strong_freqs)} strong frequencies above {threshold} dB:")
        for freq in strong_freqs:
            print(f"{freq/1e6:.3f} MHz")
        return strong_freqs

    def snap_to_fm_channel(freq_hz):
        """
        Snaps a given frequency (in Hz) to the nearest valid FM channel frequency.
        Assumes FM channels in the US from 88.1 MHz to 107.9 MHz in 200 kHz steps.
        
        Returns:
            Snapped frequency in Hz.
        """
        # Convert Hz to MHz
        freq_mhz = freq_hz / 1e6
        # Define FM band limits and channel spacing
        lower_bound = 88.1
        upper_bound = 107.9
        channel_spacing = 0.2  # MHz
        
        # Calculate the nearest channel using the lower bound as reference
        channel = round((freq_mhz - lower_bound) / channel_spacing) * channel_spacing + lower_bound
        
        # Clamp to the valid FM band
        if channel < lower_bound:
            channel = lower_bound
        if channel > upper_bound:
            channel = upper_bound

        # Return the frequency in Hz
        return channel * 1e6

    # Example usage:
    # raw_candidate = 99300000  # 99.3 MHz in Hz
    # snapped = snap_to_fm_channel(raw_candidate)

    def post_process_candidates(self, candidates):
        """
        Takes a list of candidate frequencies (in Hz) and snaps each to the nearest valid FM channel.
        Returns a sorted list of unique frequencies.
        """
        snapped = [self.snap_to_fm_channel(freq) for freq in candidates]
        # Remove duplicates and sort
        unique_snapped = sorted(set(snapped))
        return unique_snapped

    scan_thread = threading.Thread(
        target=scan_band,
        args=("FM", 88e6, 108e6, 200000, 10, 10, "fm_scan.csv"),
        daemon=True  # optional: makes the thread a daemon so it won’t block program exit
    )
    scan_thread.start()