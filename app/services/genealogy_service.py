from app import db
from app.models.animal import Animal
from app.models.breeding import ArvoreGenealogica
from collections import deque # Import deque for breadth-first traversal example

class GenealogyService:
    def calculate_inbreeding_coefficient(self, animal_id: int) -> float:
        """
        Calculates the inbreeding coefficient for a given animal.
        This requires traversing the animal's pedigree tree to identify common ancestors
        and applying Wright's coefficient of inbreeding formula or a similar algorithm.
        Will need to interact with Animal model relationships (mother, father).
        Returns the inbreeding coefficient as a float.
        """
        animal = Animal.query.get(animal_id)
        if not animal:
            # Handle case where animal is not found
            print(f"Animal with ID {animal_id} not found.")
            return 0.0 # Or raise an error

        # TODO: Implement a proper inbreeding calculation algorithm (e.g., Wright's)
        # This basic implementation is just a placeholder and does not calculate correctly.
        print(f"Calculating (placeholder) inbreeding coefficient for Animal ID: {animal_id}")
        # A proper implementation involves finding all paths to common ancestors and applying a formula.
        # Example of a highly simplified check (not accurate):
        # if animal.mother and animal.father and animal.mother.id == animal.father.id: # This checks if parents are the same animal, which is biologically impossible for different sexes
        #    return 0.25 # Example value - incorrect logic

        return 0.0 # Placeholder return value

    def generate_pedigree_tree(self, animal_id: int, depth: int = 3) -> dict:
        """
        Generates a structured representation of the pedigree tree for a given animal
        up to a specified depth.
        This involves recursively fetching parent animals.
        Returns the pedigree tree as a dictionary.
        """
        if depth < 0:
            return None

        animal = Animal.query.get(animal_id)
        if not animal:
            # Handle case where animal is not found
            print(f"Animal with ID {animal_id} not found for pedigree tree generation.")
            return None

        # Build the basic animal info
        tree = {
            'id': animal.id,
            'nome': animal.nome,
            'sexo': animal.sexo,
            'data_nascimento': animal.data_nascimento.strftime('%Y-%m-%d') if animal.data_nascimento else None,
            'mother': None,
            'father': None,
        }

        # Recursively get mother and father if they exist and depth is greater than 0
        if depth > 0:
            if animal.mother_id:
                tree['mother'] = self.generate_pedigree_tree(animal.mother_id, depth - 1)
            if animal.father_id:
                tree['father'] = self.generate_pedigree_tree(animal.father_id, depth - 1)

        return tree


    def validate_reproductive_compatibility(self, animal1_id: int, animal2_id: int) -> dict:
        """
        Validates the reproductive compatibility between two animals.
        This could involve checking for genetic conditions, calculating potential inbreeding,
        or validating against breed standards.
        Returns a dictionary indicating compatibility status and reasons.
        """
        animal1 = Animal.query.get(animal1_id)
        animal2 = Animal.query.get(animal2_id)

        if not animal1 or not animal2:
            # Handle case where one or both animals are not found
            reason = "One or both animals not found."
            if not animal1:
                reason = f"Animal 1 with ID {animal1_id} not found."
            elif not animal2:
                reason = f"Animal 2 with ID {animal2_id} not found."
            return {"compatible": False, "reason": reason}

        # TODO: Add actual compatibility logic here:
        # 1. Check for sex compatibility (usually male and female are compatible for natural breeding)
        # 2. Check for genetic health issues using associated ExameGenetico records.
        # 3. Calculate potential inbreeding coefficient of potential offspring and compare against a threshold.
        # 4. Check breed standards or other relevant criteria.

        print(f"Validating (basic) reproductive compatibility between Animal ID: {animal1_id} and Animal ID: {animal2_id}")

        # Basic check passed placeholder
        return {"compatible": True, "reason": "Basic compatibility check passed. Further genetic and inbreeding analysis recommended."}

    def find_common_ancestors(self, animal1_id: int, animal2_id: int) -> list:
        """
        Finds common ancestors between two animals.
        This involves traversing the pedigree trees of both animals upwards and identifying
        individuals present in both trees.
        Returns a list of common ancestor IDs or their names.
        """
        animal1 = Animal.query.get(animal1_id)
        animal2 = Animal.query.get(animal2_id)

        if not animal1 or not animal2:
            # Handle case where one or both animals are not found
            print(f"One or both animals not found for finding common ancestors ({animal1_id}, {animal2_id}).")
            return []

        def get_all_ancestor_ids(animal, ancestor_ids=None):
            """Helper function to recursively get all ancestor IDs."""
            if ancestor_ids is None:
                ancestor_ids = set()
            if animal:
                ancestor_ids.add(animal.id)
                # Traverse up to mother and father
                if animal.mother_id:
                    get_all_ancestor_ids(Animal.query.get(animal.mother_id), ancestor_ids)
                if animal.father_id:
                    get_all_ancestor_ids(Animal.query.get(animal.father_id), ancestor_ids)
            return ancestor_ids

        print(f"Finding common ancestors between Animal ID: {animal1_id} and Animal ID: {animal2_id}")

        ancestors1_ids = get_all_ancestor_ids(animal1)
        ancestors2_ids = get_all_ancestor_ids(animal2)

        # Find the intersection of ancestor IDs
        common_ancestor_ids = list(ancestors1_ids.intersection(ancestors2_ids))

        # Remove the animals themselves from the common ancestors list if they are the same animal
        if animal1.id in common_ancestor_ids:
             common_ancestor_ids.remove(animal1.id)
        if animal2.id in common_ancestor_ids and animal1.id != animal2.id:
             common_ancestor_ids.remove(animal2.id)

        # Optionally, fetch the common ancestor objects to return more than just IDs
        common_ancestors = Animal.query.filter(Animal.id.in_(common_ancestor_ids)).all()

        # Return a list of dictionaries with id and name for common ancestors
        return [{"id": ancestor.id, "nome": ancestor.nome} for ancestor in common_ancestors]

# Helper functions for genealogical traversal might be needed internally or in utils
# def get_all_ancestors(animal, ancestors=None):
#     if ancestors is None:
#         ancestors = set()\
#     if animal:
#         ancestors.add(animal) # Add the current animal
#         get_all_ancestors(animal.mother, ancestors)
#         get_all_ancestors(animal.father, ancestors)
#     return ancestors