import re
from typing import Any

from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    """Custom BaseModel.

    Extends Pydantic's BaseModel to automatically parse
    docstring Args blocks and set field descriptions on model initialization.
    """

    def model_post_init(self, __context: Any) -> None:
        """Automatically set field descriptions from docstring Args block.
        """
        super().model_post_init(__context)
        self._set_field_descriptions_from_docstring_args()

    def _set_field_descriptions_from_docstring_args(self) -> None:
        """Set field descriptions from Args block in class docstring.

        Parses the class docstring looking for an Args: block and extracts
        field descriptions to set on model fields that don't have descriptions.
        """
        docstring = self.__class__.__doc__
        if not docstring:
            return

        # Find the Args section - look for "Args:" followed by indented content
        args_match = re.search(
            r'\n\s*Args:\s*\n(.*?)(?:\n\s*\n|\n\s*[A-Z][a-z]+:|\Z)',
            docstring,
            re.DOTALL
        )
        if not args_match:
            return

        args_content = args_match.group(1)

        # Split into lines and process
        lines = args_content.split('\n')
        current_field = None
        current_description = []

        for line in lines:
            # Check if this line starts a new field (has field_name:)
            field_match = re.match(r'^\s*(\w+):\s*(.*)$', line)
            if field_match:
                # Save previous field if exists
                if current_field and \
                    current_field in self.__class__.model_fields:
                    self._set_field_description(
                        current_field,
                        current_description,
                    )

                # Start new field
                current_field = field_match.group(1)
                description_part = field_match.group(2).strip()
                current_description = [description_part] if \
                    description_part else []
            else:
                # Continuation of current field description
                if current_field:
                    stripped_line = line.strip()
                    if stripped_line:
                        current_description.append(stripped_line)

        # Handle the last field
        if current_field and current_field in self.__class__.model_fields:
            self._set_field_description(current_field, current_description)

    def _set_field_description(
        self,
        field_name: str,
        description_parts: list[str],
    ) -> None:
        """Set description on a model field if it doesn't already have one.
        """
        field_info = self.__class__.model_fields[field_name]
        if field_info.description is None:
            description = ' '.join(description_parts).strip()
            if description:
                field_info.description = description
