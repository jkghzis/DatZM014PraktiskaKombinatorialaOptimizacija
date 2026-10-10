"""
MAZAISPraktiskaisDarbs

Izvēlēta problēma: 9. Vakcinācijas plānošana: Problēmas apraksts: Ir k vakcinācijas centri, 
kur katram ir brīvi laika logi w[i], kad var nākt vakcinēties. Saplānot vakcināciju n cilvēkiem, 
tā, lai kopējais attālums līdz vakcinācijas centriem būtu pēc iespējas mazāks. Doti attālumi 
starp visiem cilvēkiem un centriem, kā arī katram cilvēkam ir pateikts, no cikiem līdz cikiem 
viņi tiek uz vakcināciju!

Autors:
"""
import datetime
import sys
import math
from typing import List, Optional, Tuple
import uuid
from dataclasses import dataclass, field

APP_NAME = "MAZAISPraktiskaisDarbs"
VERSION = "0.0.1"
id1 = uuid.uuid4()
"""Problem variables"""
# Vaccination center count.
K: int = 100
# Human count.
N: int = 1000
# Vaccination duration.
VACCINATION_DURATION: datetime.timedelta = datetime.timedelta(minutes=10)

"""Simulated annealing variables"""


@dataclass
class Location:
    x: float = 0.0
    y: float = 0.0

    def print(self):
        print(f"Location: ({self.x}, {self.y})")

@dataclass
class TimeWindow:
    from_time: datetime.time
    to_time: datetime.time
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    def print(self):
        print(f"TimeWindow {self.id}: {self.from_time} - {self.to_time}")

@dataclass
class AvailabilityTimeWindow:
    from_time: datetime.time
    to_time: datetime.time
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    def print(self):
        print(f"AvailabilityTimeWindow {self.id}: {self.from_time} - {self.to_time}")

@dataclass
class VacCen:
    location: Location
    time_windows: list[TimeWindow] = []
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    def print(self):
        print(f"VacCen: {self.id}")
        print(self.location.print())
        print("timeWindows:")
        for tw in self.time_windows:
            tw.print()

@dataclass
class Hum:
    location: Location
    available_time_window: AvailabilityTimeWindow
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    def print(self):
        print(f"Hum: {self.id}")
        print(self.location.print())
        print(self.available_time_window.print())

@dataclass
class Assignment:
    hum: Hum
    vacCen: VacCen
    time_window: TimeWindow
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    def print(self):
        print(f"Assginment: {self.id}")
        print(self.hum.print())
        print(self.vacCen.print())
        print(self.time_window.print())

@dataclass
class solution:
    """
    A represenation of the solution or time schedule for persons
    and vaccination centers time windows.
    
    Class contains methods required to eveluate and change the solution,
    when executing the Simulated Annealing algorithm contained in the function
    simulated_annealing().

    Returns:
        _type_: _description_
    """    
    # TODO what are the attributes/fields of the solution?
    assignments: list[Assignment] = []
    def cost(self):
        """
        Calculates the cost of the solution.

        Important: the cost function ASSUMES that the provided solution 
        adheres and is conforming to the set out constraints. The cost method 
        should be relegated to caluclating the numerical cost and not validating
        the solution. 

        Returns:
            _type_: _description_
        """        
        total_distance: float = 0.0
        # for asg in solution:
        #     person = assignment.person
        #     center = assignment.center
        #     total_distance += d(person.location, center.location)
        # return sum(
        #     distance(assignment.person.Location,
        #             assignment.vac_cen.Location)
        #     for assignment in solution
        # )
        return total_distance
    def d(self, a: Location, b: Location) -> float:
        """
        Distance function, that uses Eucleadian distance to calculate
        the distance between 2 points of type `Location`.

        Source: https://en.wikipedia.org/wiki/Euclidean_distance

        Args:
            a (Location): the first point. A persons location.
            b (Location): the second point. A vaccination centers location.

        Returns:
            float: the Eucledan distance between 2 points:
        """    
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
    def neighbor(self):
        return 0
    def move_change(self):
        return 0
    def move_swap(self):
            return 0

def simulated_annealing():
    """
    The simulated annealing function, that performs the SA
    algorithm on the defined solution in this file.

    Function controls temperature, acceptance probability, iterations, 
    and best solution.

    Returns:
        _type_: _description_
    """    
    return 0        

def main(argv: Optional[List[str]] = None) -> int:
    """Application control center and terminal process mapping."""
    if argv is None:
        argv = sys.argv[1:]
    
    
    try:
        print(f"[{APP_NAME}] Evaluation Result: ")
        return 0
    except ValueError as val_err:
        print(f"Data Input Error: {val_err}", file=sys.stderr)
        return 1
    except ArithmeticError as math_err:
        print(f"Calculation Breakdown: {math_err}", file=sys.stderr)
        return 2
    except Exception as runtime_err:
        print(f"Fatal operational exception encountered: {runtime_err}", file=sys.stderr)
        return 3

if __name__ == "__main__":
    sys.exit(main())
