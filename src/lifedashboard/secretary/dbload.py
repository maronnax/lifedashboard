import lifedashboard.model as model
import yaml
import os
import pdb

def loadBreakActivitiesFromFile(session, break_activities_file):
    break_activities_yaml = yaml.load(open(break_activities_file))

    for breakdescr in break_activities_yaml:
        for (name, initialization_dict) in breakdescr.items():
            if session.query(model.BreakActivity).filter(model.BreakActivity.name == initialization_dict['name']).count() != 0:
                continue
            break_activity = model.BreakActivity(**initialization_dict)
            session.add(break_activity)
    session.commit()
    return

def loadDatabaseData(config):
    data_directory = config.get("data_directory", is_filename=True)
    focus_directory = os.path.join(data_directory, "lifegroups")

    focus_directories = getFocusDirectories(focus_directory)

    session = model.session()

    for focus_dir in focus_directories:
        parseFocusDirectory(session, focus_dir)

    emotional_states_file = config.get("emotional_states_file", section="conf", is_filename=True, default = False)
    break_activities_file = config.get("break_activities_file", section="conf", is_filename=True, default = False)

    loadEmotionalStatesFromFile(session, emotional_states_file)
    loadBreakActivitiesFromFile(session, break_activities_file)
    session.close()
    return

def getFocusDirectories(directory):
    focus_dirs = map(lambda fn: os.path.join(directory, fn), os.listdir(directory))
    focus_dirs = filter(os.path.isdir, focus_dirs)
    focus_dirs = filter(lambda dir: "description.yaml" in os.listdir(dir), focus_dirs)
    return list(focus_dirs)

def parseFocusDirectory(session, focus_dir):
    focus_file = os.path.join(focus_dir, "description.yaml")

    focus = initializeFocusGroupFromFile(session, focus_file)

    activities_dir = os.path.join(focus_dir, "activities")
    activity_files = filter(lambda fn: fn.endswith(".yaml") and "#" not in fn, map(lambda fn: os.path.join(activities_dir, fn), os.listdir(activities_dir)))
    for fn in activity_files:
        activity_data = initializeActivityFromFile(session, fn, focus)

    return

def initializeFocusGroupFromFile(session, focus_file):

    focus_yaml = yaml.load(open(focus_file))

    focus_qry = session.query(model.FocusGroup).filter(model.FocusGroup.name == focus_yaml['name'])
    if focus_qry.count():
        # print("focus group Exists")
        focus = focus_qry.first()
    else:
        focus_disk_name = os.path.split(focus_file)[0]
        focus = model.FocusGroup(name=focus_yaml['name'], disk_name = focus_disk_name)
        session.add(focus)
        session.commit()
    return focus

def initializeActivityFromFile(session, activity_fn, parent_focus):
    activity_yaml = yaml.load(open(activity_fn))
    activity_disk_name = os.path.splitext(os.path.split(activity_fn)[1])[0]


    if session.query(model.Activity).filter(model.Activity.name == activity_yaml['name']).count():
        # print("activity Exists")
        return

    def loadOrDefault(dict, key, val):
        return dict[key] if key in dict else val

    activity_name = activity_yaml['name']
    activity_expected_pomodoro = loadOrDefault(activity_yaml, 'expected_pomodoro', 2)
    activity_progress = loadOrDefault(activity_yaml, 'progress', '0 per day')

    activity = model.Activity(name=activity_name,
                              expected_pomodoro=activity_expected_pomodoro,
                              progress = activity_progress,
                              focus_group = parent_focus,
                              disk_name = activity_disk_name)
    session.add(activity)
    session.commit()
    return


def loadEmotionalStatesFromFile(session, emotional_states_file):
    assert os.path.isfile(emotional_states_file), "Must provide conf::emotional_states_file in config"
    emotional_states = yaml.load(open(emotional_states_file))

    for (emotion, emotion_def) in emotional_states.items():
        if session.query(model.Emotion).filter(model.Emotion.name == emotion_def['name']).count():
            # print('emotion Exists')
            continue

        emotion = model.Emotion(**emotion_def)
        session.add(emotion)
    else:
        session.commit()
    return
