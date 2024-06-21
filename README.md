# Dynamic face-matching task for fMRI

![Overview](https://raw.githubusercontent.com/da-wi/dfm_fmri_task/master/instruction/dfm_fmri_task.png)

This task implements a face- and shape-matching task for fMRI in python. It is based on the original idea of Hariri et al. (2002). The faces for the task are taken with permission from the [Radboud Face Database](https://rafd.socsci.ru.nl/). If you want to use this task, you have to request access to the Radboud Face database at their website. Afterwards, contact me if you need help to generate the animated frames. 

## Installation

Requirements
- Permission to use the Radboud Face Database
- Installation of python 3.2 or higher
- Installation of pygame
- Setting the paths correctly on your system

Here is a step by step tutorial on how to install pygame:
https://www.pygame.org/wiki/GettingStarted

## Quick start

After installation of the requirements, you should be able to launch the task via the commandline:

1. Change to the correct folder (e.g. "cd /this/is/the/correct/path")
2. Call the dfm.py3 script

```
python dfm.py3 SUBJECTID -e "5,6,0,8" -o -R 4 -N 0.1 -s single
```

"SUBJECTID" is mandatory for the logfile
"-s single" enforces window mode - in the script this must be manually adjusted according to the local setup - right now this is adjusted for the MR centre in Zurich.
"-o" omits color in the symbols
"-e" sets the used emotions in this study
"-R" number of blocks
"-N" morph speed of shapes

3. Start the task by pressing "t"
4. Press the buttons "b" (left) or "y" (right) whenever you recognize the face.

## Arguments
```
david@penguin:~/dfm_fmri_task/$ python dfm.py3 --help
usage: dfm.py3 [-h] [-b BASELINE] [-c COLORTYPE] [-e EMOTIONS] [--emulation] [-f] [-l] [-i INITSTIM] [-L] [-m TESTMODE] [-n NOTRIALS] [-o]
                  [-N NONLINEAROBJECTS] [-r RUN] [-R REPETITIONS] [-s SCREENMODE] [-t TASKMODE] [-tt TRIALTIME]
                  subjectid

Dynamic face-matching task

positional arguments:
  subjectid             subject id

options:
  -h, --help            show this help message and exit
  -b BASELINE, --baseline BASELINE
                        the baseline in seconds
  -c COLORTYPE, --colortype COLORTYPE
                        [1|2] colortype 1 = black/white, colortype 2 = grey/black
  -e EMOTIONS, --emotions EMOTIONS
                        Input of emotion trials as string e.g. -e "0,5,6" 0...neutral 5...happy 6...sad
  --emulation           Sets emulation mode for use outside the scanner
  -f                    Enforce order of face trials
  -l, --forcelogdir     Force Logdir creation
  -i INITSTIM, --initstim INITSTIM
                        NOT SUPPORTED. [faces|objects] Specifies whether the paradigm starts with faces or objects, default=random
  -L                    EXPERIMENTAL! Will load all the trial images at the beginning, it will present without lag independent of baseline, but do
                        this only if enough RAM is available!! Can crash the programme.
  -m TESTMODE, --testmode TESTMODE
                        testmode
  -n NOTRIALS, --notrials NOTRIALS
                        number of trials per block
  -o, --objectman       insert interleaved object blocks (usually not needed when using -e "8" flag)
  -N NONLINEAROBJECTS, --nonlinearobjects NONLINEAROBJECTS
                        setting non-linearity offset for objects, default=1
  -r RUN, --run RUN     [1|2] determines the run number for the subject
  -R REPETITIONS, --repetitions REPETITIONS
                        specifies the number of repetitions for each block, default=4
  -s SCREENMODE, --screenmode SCREENMODE
                        [single|dual] dual or single screenmode
  -t TASKMODE, --taskmode TASKMODE
                        [dynamic|static] determines if the task is static
  -tt TRIALTIME, --trialtime TRIALTIME
                        the trialtime in seconds
```

## References

If you use this task, please cite one of the following publications:

- Willinger, D., Karipidis, I. I., Beltrani, S., Di Pietro, S. V., Sladky, R., Walitza, S., ... & Brem, S. (2019). Valence-dependent coupling of prefrontal-amygdala effective connectivity during facial affect processing. _eNeuro_, 6(4).

- Willinger, D., Karipidis, I. I., Häberling, I., Berger, G., Walitza, S., & Brem, S. (2022). Deficient prefrontal-amygdalar connectivity underlies inefficient face processing in adolescent major depressive disorder. _Translational Psychiatry_, 12(1), 195.  

- Langner, O., Dotsch, R., Bijlstra, G., Wigboldus, D. H., Hawk, S. T., & Van Knippenberg, A. D. (2010). Presentation and validation of the Radboud Faces Database. _Cognition and emotion_, 24(8), 1377-1388.