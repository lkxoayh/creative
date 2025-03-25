import itertools
import string
import os.path
import pickle
import time
import ctypes
import glob
import sys

# Configuration
KEYWORDS_DIR = './keywords'
DEFAULT_LENGTH = 6
keywords_file = f'{KEYWORDS_DIR}/keywords_{DEFAULT_LENGTH}.pkl'

# Function to set console title (Windows specific)
def set_cmd_title(title):
    """Set Windows console title"""
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    except:
        # Silently fail if not running on Windows
        pass

def iter_all_strings():
    """Generate all possible strings starting with all lowercase letters."""
    for size in itertools.count(3):
        for first_letter in string.ascii_lowercase:  # Use all lowercase letters
            for s in itertools.product(string.ascii_lowercase, repeat=size-1):
                yield first_letter + "".join(s)

def calculate_keyword_stats(length):
    """Calculate statistics for keyword generation of given length."""
    total_keywords = sum(26 * 26**(i-1) for i in range(3, length+1))
    # Estimate size in memory (rough estimate: each string is ~8 bytes per char + overhead)
    avg_char_count = (3 + length) / 2  # Average string length
    estimated_bytes_per_keyword = avg_char_count * 8 + 32  # String overhead
    estimated_total_size_bytes = total_keywords * estimated_bytes_per_keyword
    
    # Convert to human-readable sizes
    size_units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
    size_value = estimated_total_size_bytes
    unit_index = 0
    while size_value > 1024 and unit_index < len(size_units) - 1:
        size_value /= 1024
        unit_index += 1
    
    return {
        'total_keywords': total_keywords,
        'size_value': size_value,
        'size_unit': size_units[unit_index],
        'estimated_time_hours': total_keywords / (500000 * 3600)  # Rough estimate based on 500K keywords/hr
    }

def get_keywords(count: int):
    """Generate keywords up to specified count (length)."""
    # Ensure the keywords directory exists
    os.makedirs(KEYWORDS_DIR, exist_ok=True)
    
    letter_list = []
    # Calculate total keywords for all 26 letters
    total_keywords = sum(26 * 26**(i-1) for i in range(3, count+1))
    start_time = time.time()
    update_interval = 10000  # Update title every 10,000 keywords
    batch_size = 500000  # Save to disk after this many keywords
    
    print(f"Will generate approximately {total_keywords:,} keywords in total")
    set_cmd_title(f"Keyword Generator - Starting...")
    
    try:
        for idx, s in enumerate(iter_all_strings(), 1):
            letter_list.append(s)
            
            # Update command title periodically
            if idx % update_interval == 0:
                elapsed = time.time() - start_time
                speed = idx / elapsed if elapsed > 0 else 0
                percent = (idx / total_keywords) * 100 if total_keywords > 0 else 0
                eta_seconds = (total_keywords - idx) / speed if speed > 0 else 0
                
                # Format ETA nicely
                eta_str = ""
                if eta_seconds > 86400:  # days
                    eta_str = f"{eta_seconds/86400:.1f} days"
                elif eta_seconds > 3600:  # hours
                    eta_str = f"{eta_seconds/3600:.1f} hours"
                elif eta_seconds > 60:  # minutes
                    eta_str = f"{eta_seconds/60:.1f} minutes"
                else:
                    eta_str = f"{eta_seconds:.0f} seconds"
                    
                status = f"Keyword Generator - {idx:,}/{total_keywords:,} ({percent:.2f}%) - ETA: {eta_str}"
                set_cmd_title(status)
                
                # Also print progress occasionally
                if idx % (update_interval * 10) == 0:
                    print(f"Progress: {idx:,} keywords ({percent:.2f}%) - {speed:.2f} keys/sec - ETA: {eta_str}")
            
            # Save in batches to prevent memory issues
            if idx % batch_size == 0:
                temp_filename = f"{KEYWORDS_DIR}/keywords_batch_{idx}.pkl"
                print(f"Saving batch of {len(letter_list):,} keywords to {temp_filename}...")
                save_keywords(letter_list, temp_filename)
                letter_list = []  # Clear list after saving
            
            # End condition to stop at zzzz...
            if s == 'z' + 'z'*(count-1):
                # Save remaining keywords
                if letter_list:
                    temp_filename = f"{KEYWORDS_DIR}/keywords_final_batch.pkl"
                    save_keywords(letter_list, temp_filename)
                break
        
        # Set final title
        set_cmd_title(f"Keyword Generator - Complete! Generated {idx:,} keywords")
        
        # Merge all batches and save to final file
        print("Generation complete. Merging all batches...")
        merged_keywords = merge_temp_files()
        if merged_keywords:
            save_keywords(merged_keywords, keywords_file)
            return merged_keywords
        return letter_list
    
    except MemoryError:
        # Save what we have so far before running out of memory
        if letter_list:
            emergency_filename = f"{KEYWORDS_DIR}/keywords_emergency.pkl"
            print(f"Memory error! Saving emergency batch to {emergency_filename}...")
            try:
                save_keywords(letter_list, emergency_filename)
                print(f"Successfully saved {len(letter_list):,} keywords to {emergency_filename}")
            except:
                print("Could not save emergency batch - memory completely exhausted")
        
        print(f"Memory error occurred. Progress saved up to batch size")
        return None
    
    except KeyboardInterrupt:
        # Handle user interruption
        print("\nProcess interrupted by user!")
        if letter_list:
            interrupt_filename = f"{KEYWORDS_DIR}/keywords_interrupted.pkl"
            print(f"Saving current batch to {interrupt_filename}...")
            try:
                save_keywords(letter_list, interrupt_filename)
                print(f"Successfully saved {len(letter_list):,} keywords to {interrupt_filename}")
            except Exception as e:
                print(f"Failed to save interrupted batch: {e}")
        return None
    
    except Exception as e:
        # Handle other exceptions
        if letter_list:
            emergency_filename = f"{KEYWORDS_DIR}/keywords_error.pkl"
            print(f"Error! Saving emergency batch to {emergency_filename}...")
            try:
                save_keywords(letter_list, emergency_filename)
            except:
                print("Could not save emergency batch")
        
        print(f"Error: {e}")
        return None

def save_keywords(keywords, filename):
    """Save keywords list to a file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    print(f"Saving {len(keywords):,} keywords to {filename}...")
    set_cmd_title(f"Keyword Generator - Saving {len(keywords):,} keywords...")
    
    try:
        with open(filename, 'wb') as f:
            pickle.dump(keywords, f)
        print(f"Keywords saved to {filename}")
        set_cmd_title(f"Keyword Generator - Saved {len(keywords):,} keywords")
        return True
    except Exception as e:
        print(f"Error saving keywords: {e}")
        return False

def load_keywords(filename):
    """Load keywords list from a file."""
    if os.path.exists(filename):
        print(f"Loading keywords from {filename}...")
        set_cmd_title(f"Keyword Generator - Loading keywords...")
        
        try:
            with open(filename, 'rb') as f:
                keywords = pickle.load(f)
            
            set_cmd_title(f"Keyword Generator - Loaded {len(keywords):,} keywords")
            return keywords
        except Exception as e:
            print(f"Error loading keywords from {filename}: {e}")
            return None
    return None

def merge_temp_files():
    """Merge all temporary keyword files into one."""
    # Find all temporary keyword files
    temp_files = glob.glob(f'{KEYWORDS_DIR}/keywords_batch_*.pkl')
    final_batch = glob.glob(f'{KEYWORDS_DIR}/keywords_final_batch.pkl')
    temp_files.extend(final_batch)
    
    if not temp_files:
        return None
    
    print(f"Found {len(temp_files)} temporary keyword files to merge")
    set_cmd_title(f"Keyword Generator - Merging {len(temp_files)} files...")
    
    all_keywords = []
    # Sort files based on their number to maintain proper order
    for file in sorted(temp_files, key=lambda x: int(x.split('_')[2].split('.')[0]) if 'batch_' in x else float('inf')):
        print(f"Loading {file}...")
        try:
            with open(file, 'rb') as f:
                keywords = pickle.load(f)
                all_keywords.extend(keywords)
                print(f"Added {len(keywords):,} keywords from {file}")
            
            # Optionally delete the file after merging
            # os.remove(file)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    print(f"Merged a total of {len(all_keywords):,} keywords")
    return all_keywords

# Main execution
if __name__ == "__main__":
    # Ensure keyword directory exists
    os.makedirs(KEYWORDS_DIR, exist_ok=True)
    
    # Check if length is specified
    if len(sys.argv) > 1:
        try:
            length = int(sys.argv[1])
            set_keyword_length(length)
            print(f"Using keyword length: {length}")
        except ValueError:
            print(f"Invalid length argument: {sys.argv[1]}. Using default length {DEFAULT_LENGTH}.")
    
    # Try to load keywords first
    keywords = load_keywords(keywords_file)
    
    # If not found, check for recovery options or generate new keywords
    if keywords is None:
        # Check for emergency files first
        emergency_files = [
            f"{KEYWORDS_DIR}/keywords_emergency.pkl",
            f"{KEYWORDS_DIR}/keywords_interrupted.pkl",
            f"{KEYWORDS_DIR}/keywords_error.pkl"
        ]
        
        for emergency_file in emergency_files:
            if os.path.exists(emergency_file):
                print(f"Found recovery file {emergency_file}")
                emergency_keywords = load_keywords(emergency_file)
                if emergency_keywords:
                    print(f"Loaded {len(emergency_keywords):,} keywords from recovery file")
                    keywords = emergency_keywords
                    break
                
        # Check for temporary batch files
        if keywords is None:
            print("Checking for temporary batch files...")
            merged_keywords = merge_temp_files()
            if merged_keywords:
                print(f"Merged {len(merged_keywords):,} keywords from temporary files")
                # Ask if user wants to save these
                save_choice = input("Save merged keywords to main file? (y/n): ").strip().lower()
                if save_choice == 'y':
                    save_keywords(merged_keywords, keywords_file)
                    keywords = merged_keywords
                    
                    # Ask about cleaning up temp files
                    cleanup_choice = input("Clean up temporary files? (y/n): ").strip().lower()
                    if cleanup_choice == 'y':
                        clean_temp_files(confirm=False)
        
        # Generate new keywords if nothing was loaded
        if keywords is None:
            length = int(keywords_file.split('_')[-1].split('.')[0])  # Extract length from filename
            print(f"Generating keywords of length {length} (this may take some time)...")
            
            # Calculate and display statistics
            stats = calculate_keyword_stats(length)
            print(f"Using all 26 lowercase letters will generate approximately {stats['total_keywords']:,} keywords")
            print(f"Estimated storage size: {stats['size_value']:.2f} {stats['size_unit']}")
            print(f"Estimated generation time: {stats['estimated_time_hours']:.1f} hours")
            
            continue_choice = input("This might take a very long time. Continue? (y/n): ").strip().lower()
            if continue_choice == 'y':
                try:
                    keywords = get_keywords(length)
                    if keywords:
                        print(f"Generation complete. Total keywords: {len(keywords):,}")
                        
                        # Ask about cleaning up temp files
                        cleanup_choice = input("Clean up temporary files? (y/n): ").strip().lower()
                        if cleanup_choice == 'y':
                            clean_temp_files(confirm=False)
                except KeyboardInterrupt:
                    print("\nKeyword generation interrupted by user.")
                except Exception as e:
                    print(f"An error occurred during generation: {e}")
                    
                    # Check again for any emergency files that might have been created
                    for emergency_file in emergency_files:
                        if os.path.exists(emergency_file):
                            print(f"Found recovery file {emergency_file}")
                            emergency_keywords = load_keywords(emergency_file)
                            if emergency_keywords:
                                print(f"Loaded {len(emergency_keywords):,} keywords from recovery file")
                                keywords = emergency_keywords
                                break
            else:
                print("Generation cancelled by user.")
    else:
        print(f"Loaded {len(keywords):,} keywords from file")
    
    # Print the first 10 keywords as a sample
    if keywords:
        print(f"Sample of keywords (total: {len(keywords):,}): {keywords[:10]}")
    else:
        print("No keywords were generated or loaded.")
    
    # Reset the title when done
    set_cmd_title("Keyword Generator - Done")

# You can access all keywords by calling:
# all_keywords = load_keywords(keywords_file)

# Simple variable that loads all keyboards