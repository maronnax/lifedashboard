"""Model for the application"""

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy import Enum
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy import Float
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func
from sqlalchemy import Table
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.schema import UniqueConstraint
import datetime
import os
import pdb

initialized = False
engine = False
Session = False

class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    id =  Column(Integer, primary_key=True)

    @staticmethod
    def simpleStrftime(tm):
        return tm.strftime("%b-%d %a %H%M")

class CreatedAtMixin(object):
    created_at = Column(DateTime, default=func.now())

Base = declarative_base(cls=Base)

class FocusGroup(Base, CreatedAtMixin):
    name = Column(String, unique = True, nullable = False)
    activities = relationship("Activity", backref="focus_group")

    def __repr__(self):
        return "{}".format(self.name)

class Pomodoro(Base, CreatedAtMixin):
    start_time = Column(DateTime, nullable = False)
    end_time = Column(DateTime, nullable = False)
    message = Column(String)
    activity_record_id = Column(Integer, ForeignKey("activityrecord.id"), nullable=False)
    def __repr__(self):
        return "Pom {}, {}: {} - {}".format(self.id, self.activity_record.activity.name, self.start_time.strftime("%b-%d %H%M"), self.end_time.strftime("%H%M"))

class ActivityRecord(Base, CreatedAtMixin):
    start_time = Column(DateTime, nullable = False)
    end_time = Column(DateTime)
    message = Column(String)
    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=True)

    pomodoros = relationship("Pomodoro", backref='activity_record')
    def __repr__(self):
        if self.end_time is None:
            return "{}: {} - *".format(self.activity.name, self.start_time.strftime("%b-%d %H%M"), self.start_time.strftime("%H%M"))
        elif (self.start_time - self.end_time).total_seconds() < (15 * 60):
            return "{}: {} ".format(self.activity.name, self.start_time.strftime("%b-%d %H%M"))
        else:
            return "{}: {} - {}".format(self.activity.name, self.start_time.strftime("%b-%d %H%M"), self.end_time.strftime("%H%M"))


def parseProgress(progress):
    components = progress.split()
    total = int(components[0])
    assert components[1] == "per"
    assert components[2] in ["day", "week", "month"]
    return (total, components)

# emotion_target_states = Table('emotion_target_states', Base.metadata,
#                               Column('emotionaltarget_id', Integer, ForeignKey('emotionaltarget.id')),
#                               Column('emotion_id', Integer, ForeignKey('emotion.id')))

emotion_states = Table('emotion_states', Base.metadata,
                       Column('emotionalstate_id', Integer, ForeignKey('emotionalstate.id')),
                       Column('emotion_id', Integer, ForeignKey('emotion.id')))

# class EmotionalTarget(Base, CreatedAtMixin):
#     name = Column(String, nullable = False)
#     description = Column(String, nullable = True)
#     emotions = relationship("Emotion", secondary="emotion_states", back_populates="emotional_states")

class EmotionalState(Base, CreatedAtMixin):
    time = Column(DateTime, nullable = False)
    description = Column(String)
    emotions = relationship("Emotion", secondary="emotion_states", back_populates="emotional_states")

    def __repr__(self):
        emotion_string = ", ".join(map(lambda emot: emot.name, self.emotions))
        repr_string = "{} - {}".format(self.simpleStrftime(self.time), emotion_string)

        if self.description:
            repr_string += " - {}".format(self.description)

        return repr_string

    @classmethod
    def createEmotionalState(cls, session):
        now = datetime.datetime.utcnow()

        emotions = cls.selectEmotions(session)
        desription = cls.getOptionalDescription()

        emotional_state = cls(time = now, emotions = emotions, description = desription)
        return emotional_state

    @staticmethod
    def selectEmotions(session):
        emotions = session.query(Emotion).order_by(Emotion.state.desc(), Emotion.name).all()
        for (ndx, emotion) in enumerate(emotions):
            print("{}: {}".format(ndx+1,emotion.name))

        emotion_select_string = input("Select emotions: ")
        selected_emotions = [emotions[int(ndx)-1] for ndx in emotion_select_string.split(",") if ndx.strip()]

        return selected_emotions

    @staticmethod
    def getOptionalDescription():
        description = input("Describe? ").lower().strip()
        if description.startswith("y") or not description:
            return input("> ")
        else:
            return ""

class Emotion(Base, CreatedAtMixin):
    name = Column(String, nullable = False)
    state = Column(Integer, nullable = False, default = 0)
    emotional_states = relationship("EmotionalState", secondary="emotion_states", back_populates="emotions")
    # emotional_targets = relationship("EmotionalTarget", secondary="emotion_target_states", back_populates="emotions")
    # preactivity_states = relationship("ActivityRecord", secondary="preactivity_emotional_states", back_populates="initial_emotions")

    def __repr__(self):
        return "{} ({})".format(self.name, self.state)

class Activity(Base, CreatedAtMixin):
    name = Column(String, nullable = False)
    expected_pomodoro = Column(Integer)
    progress = Column(String)
    active = Column(Boolean, default = True)
    focusgroup_id = Column(Integer, ForeignKey("focusgroup.id"), nullable=True)
    records = relationship("ActivityRecord", backref="activity")

    def __repr__(self):
        return "{} ({} hrs)".format(self.name, self.expected_time)

    expected_time = property(lambda self: self.expected_pomodoro/2)

def initializeDatabase():
    global initialized
    global engine

    print("Loading db schema.")
    assert initialized, 'Module db connection must be initialized before a db can be created.'
    Base.metadata.create_all(engine)

    return True

def initializeModule():
    global engine
    global Session
    global initialized

    #db_connection_str = config.generateDBConnectionStringFromConfig(config_obj)
    # engine = create_engine(db_connection_str)

    # engine = create_engine('sqlite:///:memory:', echo=True)

    db_file = "/Users/naddy/Source/lifedashboard/db/secretary.db"
    initialize = False
    if not os.path.isfile(db_file):
        # os.remove(db_file)
        initialize = True
    engine = create_engine('sqlite:///{0}'.format(db_file))
    Session = sessionmaker(bind=engine)
    initialized = True
    if initialize: initializeDatabase()


    return True

initializeModule()
# initializeDatabase()

def session():
    return Session()
