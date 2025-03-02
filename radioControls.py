import subprocess
import csv
import time
import os

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
    cmd = f"rtl_power -f {start_freq}:{end_freq}:{step} -i {integration_time} -E 1 -F csv > {output_csv}"
    print("Running command:", cmd)
    
    # Run the command (blocking call).
    subprocess.run(cmd, shell=True)
    # Give a short delay to ensure the file is written.
    time.sleep(1)
    
    candidates = []
    if os.path.exists(output_csv):
        with open(output_csv, newline='') as csvfile:
            reader = csv.reader(csvfile)
            # Example CSV row: "Frequency, Power" (adjust indices as needed)
            for row in reader:
                try:
                    freq = float(row[0])
                    power = float(row[1])
                    # If the measured power is above our threshold, add to candidates.
                    if power > threshold:
                        candidates.append(freq)
                except Exception as e:
                    # Skip header lines or malformed rows.
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
