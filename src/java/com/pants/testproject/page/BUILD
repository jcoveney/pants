# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

page(name="readme",
     source="README.md",
     dependencies=['src/java/com/pants/examples/hello/main:readme'],
       provides=[
           wiki_artifact(wiki=pants('//:confluence'),
	         space='ENG',
		       title='Linker and Furthermore',
		             parent='pants_page',
			         )
]
     )