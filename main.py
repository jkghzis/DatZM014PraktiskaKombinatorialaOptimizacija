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
import random
from pprint import pprint

APP_NAME = "MAZAISPraktiskaisDarbs"
VERSION = "0.0.1"
id1 = uuid.uuid4()
"""Problem variables"""
# Vaccination center count.
K: int = 5
# Human count.
N: int = 10
# Vaccination duration.
VACCINATION_DURATION: datetime.timedelta = datetime.timedelta(minutes=10)

"""Simulated annealing variables"""
INITIAL_TEMPERATURE: float = 100.0
COOLING_RATE: float = 0.95 # Using geometric cooling, instead of linear cooling.
ITERATION_PER_TEMPERATURE: int = 100
MINIMUM_TEMPERATURE: float = 0.01
MAX_NEIGHBOR_ATTEMPTS: int = 50

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
    time_windows: list[TimeWindow] = field(default_factory=list)
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
    vac_cen: VacCen
    time_window: TimeWindow
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    def print(self):
        print(f"Assginment: {self.id}")
        print(self.hum.print())
        print(self.vac_cen.print())
        print(self.time_window.print())

def d(a: Location, b: Location) -> float:
    """
    Distance function, that uses Eucleadian distance to calculate
    the distance between 2 points of type `Location`.

    Source: https://en.wikipedia.org/wiki/Euclidean_distance

    Args:
        a (Location): the first point. A persons location.
        b (Location): the second point. A vaccination centers location.

    Returns:
        float: the Eucledan distance between 2 points
    """    
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

@dataclass
class Solution:
    """
    A represenation of 1 complete vaccination schedule for persons
    and vaccination centers time windows.
    
    Class contains methods required to eveluate and change the solution,
    when executing the Simulated Annealing algorithm contained in the function
    simulated_annealing().

    The class also holds the humans and vaccination centers currently
    used for calculating teh assignments. This is mainly for validation
    and cost calculation.
    """    
    hums: list[Hum] # Allows to validate that all humans have an appointment.
    vac_cens: list[VacCen] # Keeps track of all available vaccination centers and their slots (including not assigned centers and slots).
    assignments: list[Assignment] = field(default_factory=list)
    def is_valid(self) -> bool:
        """
        Check the validity of a solution given a set of constraints.
        
        Constraints:
        1. Katrai personai ir piešķirts tieši 1 pieraksts uz vakcinācijas centru;
        2. Piešķirtam vakcinācijas laika logam pilnībā jāietilpst personas pieejamības periodā;
        3. Viens laika logs vakcinācijas centrā var būt pieškirt ne vairāk kā vienai personai dotā grafikā;
        4. Piešķirtajam laika logam ir jābūt pieejamam izvēlētajā vakcinācijas centrā
        """        
        # 1. Every required person has exactly one assignment.
        # Check both the number of assignments and the identity of each person.
        human_ids = {hum.id for hum in self.hums}
        assigned_human_ids = [asg.hum.id for asg in self.assignments]
        if len(assigned_human_ids) != len(human_ids):
            return False
        if set(assigned_human_ids) != human_ids:
            return False
        # The set comparison above doesn't detect duplicate assignments
        # if the total number happens to match, so check uniqueness too.
        if len(assigned_human_ids) != len(set(assigned_human_ids)):
            return False

        # 2. Each appointment fits entirely within the person's availability.
        for asg in self.assignments:
            if not (
                asg.time_window.from_time 
                    >= asg.hum.available_time_window.from_time 
                and asg.time_window.to_time 
                    <= asg.hum.available_time_window.to_time
            ):
               return False

        # 3. Each appointment slot is assigned at most once.
        time_window_ids = [asg.time_window.id for asg in self.assignments]
        if len(time_window_ids) != len(set(time_window_ids)): # Check for uniqueness
            return False
        
        # 4. Each appointment slot belongs to the assigned center.
        for asg in self.assignments:
            center_slot_ids = {
                tw.id for tw in asg.vac_cen.time_windows
            }
            if asg.time_window.id not in center_slot_ids:
                return False

        return True

    def cost(self) -> float:
        """
        Calculates the cost of the solution.

        Important: the cost function ASSUMES that the provided solution 
        adheres and is conforming to the set out constraints. The cost method 
        should be relegated to caluclating the numerical cost and not validating
        the solution. 

        Note: It doesn't decide whether to accept a cost or cool the temperature; 
        those are responsibilities of the SA algorithm.

        Returns:
            float: the total distance for the solution
        """        
        return sum(d(asg.hum.location, asg.vac_cen.location) for asg in self.assignments)

    def neighbor(self) -> Optional["Solution"]: 
        """
        Returns a new neighboring solution.

        Uses MAX_NEIGHBOR_ATTEMPTS.

        It acts as a small dispatcher:
        1. Randomly choose between move_change() and move_swap().
        2. Attempt the chosen move.
        3. If it fails, optionally try the other move type or retry a limited number of times.
        4. Return the resulting valid neighbor, or None.

        Possible moves:
        - change: nejauši izvēlētai personai tiek nomainīts pieraksts vakcinācijas centrā uz citu, 
          brīvu pierakstu citā vakcinācijas centrā vai vienā un tajā pašā vakcinācijas centrā, 
          kas pilnībā ietilpst personas pieejamības periodā;
        - swap: nejauši izvēlētām divām personām tiek apmainīti vakcinācijas pieraksti, 
          ja pēc apmaiņas tiek ievēroti visi ierobežojumi.

        Returns:
            list[Assignment]: a new schedule/solution
        """      
        for _ in range(MAX_NEIGHBOR_ATTEMPTS):
            move = random.choice([
                self.move_change,
                self.move_swap
            ])
            
            candidate = move()
            
            if candidate is not None:
                return candidate
        
        return None
    
    def move_change(self) -> Optional["Solution"]: 
        """
        Randomly moves 1 Hum to another VacCen TimeWindow or to a TimeWindow
        of the current VacCen.
        1. Select a person randomly.
        2. Find appointment slots that are free and fit that person's availability.
        3. Select one of those slots, potentially at the same center or another center.
        4. Create a new schedule with that person's assignment changed.
        5. Return the new schedule, or None if no valid move can be found.
        """        
        if not self.assignments:
            return None
        # 1. Select a person randomly who already has an assignment.
        current_assignment = random.choice(self.assignments)
        selected_hum = current_assignment.hum
        # 2. Find slots currently used by OTHER people.
        used_slot_ids = { asg.time_window.id for asg in self.assignments if asg.hum.id != selected_hum.id }
        # 3. Find free slots that fit this person's availability.
        candidates: list[tuple[VacCen, TimeWindow]] = []

        for center in self.vac_cens:
            for slot in center.time_windows:
                # If slot is already used.
                if slot.id in used_slot_ids:
                    continue
                # If slots from_time doesn't work for the selected_hum.
                if slot.from_time < selected_hum.available_time_window.from_time:
                    continue
                # If slots to_time doesn't work for the selected_hum.
                if slot.to_time > selected_hum.available_time_window.to_time:
                    continue
                # Don't return the exact same appointment.
                if (slot.id == current_assignment.time_window.id and center.id == current_assignment.vac_cen.id):
                    continue
                # Center is already related to slot per the for loops definition.
                candidates.append((center, slot))
    
        if not candidates:
            return None

        # 4. Choose a new center and slot.
        new_center, new_slot = random.choice(candidates)

        # 5. Construct a new list of assignments.
        new_assignments = [
            Assignment(
                hum = asg.hum,
                vac_cen = new_center if asg.hum.id == selected_hum.id else asg.vac_cen,
                time_window = new_slot if asg.hum.id == selected_hum.id else asg.time_window
            )
            for asg in self.assignments
        ]

        # 6. Construct and validate the neighboring solution.
        candidate_solution = Solution(
            hums=self.hums,
            vac_cens=self.vac_cens,
            assignments=new_assignments
        )

        # 7. Only return solution, if its valid.
        if candidate_solution.is_valid():
            return candidate_solution

        # 8. If no valid solution was identified, then return nothing.
        # A new solution will be attempted.
        return None

    def move_swap(self) -> Optional["Solution"]: 
        """
        Randomly swaps 2 Hum VacCen, TimeWindows with each other.
        1. Select two different people.
        2. Propose exchanging their appointments.
        3. Check whether each person's new appointment fits their availability.
        4. Construct a new schedule and validate it.
        5. Return the new schedule, or None if the move is invalid.
        """        
        if len(self.assignments) < 2:
            return None

        # 1. Select two different people.
        first, second = random.sample(self.assignments, 2)

        # 2. Exchange their appointments, leaving the people unchanged.
        new_assignments = []

        for asg in self.assignments:
            if asg.hum.id == first.hum.id:
                new_assignments.append(
                    Assignment(
                        hum=asg.hum,
                        vac_cen=second.vac_cen,
                        time_window=second.time_window
                    )
                )
            elif asg.hum.id == second.hum.id:
                new_assignments.append(
                    Assignment(
                        hum=asg.hum,
                        vac_cen=first.vac_cen,
                        time_window=first.time_window
                    )
                )
            else:
                new_assignments.append(
                    Assignment(
                        hum=asg.hum,
                        vac_cen=asg.vac_cen,
                        time_window=asg.time_window
                    )
                )

        # 3. Construct the candidate schedule.
        candidate_solution = Solution(
            hums=self.hums,
            vac_cens=self.vac_cens,
            assignments=new_assignments
        )

        # 4. Construct a new schedule and validate it.
        # 5. Return the new schedule, or None if the move is invalid.
        if candidate_solution.is_valid():
            return candidate_solution

        return None

def generate_synthetic_data() -> tuple[
    list[Hum],
    list[VacCen],
    list[Assignment]
]:
    """
    Generate synthetic people, vaccination centers, and a guaranteed
    feasible initial set of assignments.

    Returns:
        humans, vac_cens, guaranteed_assignments
    """
    day_start = datetime.datetime.combine(
        datetime.date(2026, 1, 1),
        datetime.time(9, 0)
    )
    day_end = datetime.datetime.combine(
        datetime.date(2026, 1, 1),
        datetime.time(17, 0)
    )
    if VACCINATION_DURATION <= datetime.timedelta(0):
        raise ValueError("Vaccination duration must be positive.")

    day_duration = day_end - day_start

    if day_duration % VACCINATION_DURATION != datetime.timedelta(0):
        raise ValueError(
            "Vaccination duration must divide the working day evenly."
        )

    slots_per_center = day_duration // VACCINATION_DURATION

    if K <= 0 or N <= 0:
        raise ValueError("K and N must both be positive.")

    # 1. Generate vaccination centers and their appointment slots.
    vac_cens: list[VacCen] = []
    all_slots: list[tuple[VacCen, TimeWindow, int]] = []

    for _ in range(K):
        center = VacCen(
            location=Location(
                x=random.uniform(0, 100),
                y=random.uniform(0, 100)
            )
        )

        for slot_index in range(slots_per_center):
            start = day_start + (VACCINATION_DURATION * slot_index)
            end = start + VACCINATION_DURATION
            slot = TimeWindow(from_time=start.time(), to_time=end.time())
            center.time_windows.append(slot)
            all_slots.append((center, slot, slot_index))

        vac_cens.append(center)

    # 2. Ensure enough slots exist to schedule everyone.
    if N > len(all_slots):
        raise ValueError(
            f"Cannot schedule {N} people: only "
            f"{len(all_slots)} slots exist."
        )

    # 3. Choose N distinct slots as guaranteed appointments.
    selected_slots = random.sample(all_slots, N)

    hums: list[Hum] = []
    guaranteed_assignments: list[Assignment] = []

    # 4. Give each person availability containing their chosen slot.
    for center, slot, slot_index in selected_slots:
        # Allow availability to extend up to 2 hours before/after
        # the guaranteed appointment, within the working day.
        earliest_index = max(
            0,
            slot_index - 120 // (VACCINATION_DURATION.seconds // 60)
        )
        latest_index = min(
            slots_per_center,
            slot_index + 1
            + 120 // (VACCINATION_DURATION.seconds // 60)
        )

        availability_start_index = random.randint(
            earliest_index, slot_index
        )
        availability_end_index = random.randint(
            slot_index + 1, latest_index
        )

        availability_start = (
            day_start
            + VACCINATION_DURATION * availability_start_index
        )
        availability_end = (
            day_start
            + VACCINATION_DURATION * availability_end_index
        )

        hum = Hum(
            location=Location(
                x=random.uniform(0, 100),
                y=random.uniform(0, 100)
            ),
            available_time_window=AvailabilityTimeWindow(
                from_time=availability_start.time(),
                to_time=availability_end.time()
            )
        )

        hums.append(hum)

        guaranteed_assignments.append(
            Assignment(
                hum=hum,
                vac_cen=center,
                time_window=slot
            )
        )

    return hums, vac_cens, guaranteed_assignments

def build_initial_solution(
    hums: list[Hum],
    vac_cens: list[VacCen],
    guaranteed_assignments: list[Assignment]
) -> Solution:
    """
    Construct and validate the guaranteed feasible initial solution.
    """
    initial_solution = Solution(hums=hums, vac_cens=vac_cens, assignments=guaranteed_assignments)
    if not initial_solution.is_valid():
        raise RuntimeError("Generated initial solution unexpectedly violates constraints.")

    return initial_solution

def simulated_annealing(initial_solution: Solution) -> Solution:
    """
    The simulated annealing function, that performs the SA
    algorithm on the defined solution in this file.

    Function controls temperature, acceptance probability, iterations, 
    and best solution.

    Returns:
        _type_: _description_
    """    
    # 1. Validate the initial state and algorithm parameters.
    if not initial_solution.is_valid():
        raise ValueError("The initial solution must be valid.")

    if INITIAL_TEMPERATURE <= 0:
        raise ValueError("Initial temperature must be positive.")

    if not 0 < COOLING_RATE < 1:
        raise ValueError("Cooling rate must be between 0 and 1.")

    if not 0 < MINIMUM_TEMPERATURE < INITIAL_TEMPERATURE:
        raise ValueError("Minimum temperature must be positive and below the initial temperature.")

    if ITERATION_PER_TEMPERATURE <= 0:
        raise ValueError("Iterations per temperature must be positive.")

    # 2. Initialize the current and best solutions.
    current_solution = initial_solution
    best_solution = initial_solution

    current_cost = current_solution.cost()
    best_cost = current_cost

    temperature = INITIAL_TEMPERATURE

    # 3. Repeat the search while the temperature is high enough.
    while temperature > MINIMUM_TEMPERATURE:

        for _ in range(ITERATION_PER_TEMPERATURE):

            # Pick a random neighboring solution.
            candidate = current_solution.neighbor()

            # No valid neighbor was found during this attempt.
            if candidate is None:
                continue

            candidate_cost = candidate.cost()
            delta = candidate_cost - current_cost

            # 4. Decide whether to accept the candidate.
            if delta <= 0 or random.random() < math.exp(-delta / temperature):
                current_solution = candidate
                current_cost = candidate_cost

                # Keep track of the best solution ever encountered.
                if candidate_cost < best_cost:
                    best_solution = candidate
                    best_cost = candidate_cost

        # 5. Cool the system using geometric cooling.
        temperature *= COOLING_RATE

    # 6. Return the best solution found, not necessarily the last one.
    return best_solution       

def main(argv: Optional[List[str]] = None) -> int:
    """Application control center and terminal process mapping."""
    if argv is None:
        argv = sys.argv[1:]
    try:
        print(f"[{APP_NAME}] Result: ")
        # hums, vac_cens, guaranteed_assignments = generate_synthetic_data()
        # initial_solution = build_initial_solution(
        #     hums,
        #     vac_cens,
        #     guaranteed_assignments
        # )
        # print("Valid:", initial_solution.is_valid())
        # print("People:", len(initial_solution.hums))
        # print("Centers:", len(initial_solution.vac_cens))
        # print("Assignments:", len(initial_solution.assignments))
        # print("Initial cost:", initial_solution.cost()) 
        # # pprint(vars(initial_solution), indent=4, width=120)
        hums, vac_cens, guaranteed_assignments = generate_synthetic_data()
        initial_solution = build_initial_solution(
            hums,
            vac_cens,
            guaranteed_assignments
        )
        initial_cost = initial_solution.cost()
        best_solution = simulated_annealing(initial_solution)
        best_cost = best_solution.cost()
        print("Initial valid:", initial_solution.is_valid())
        print("Result valid:", best_solution.is_valid())
        print("Initial cost:", initial_cost)
        print("Final best cost:", best_cost)
        print("Improvement:", initial_cost - best_cost)
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
