import subprocess


process = subprocess.Popen(
    ['celery', '-A', 'main', 'worker', '--pool=solo'],
)

process_beat = subprocess.Popen(
        ['celery', '-A', 'main', 'beat', "--loglevel=info"]
)

process.wait()
process.wait()