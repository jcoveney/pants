# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os
import re
import subprocess

from pants.base.build_environment import get_buildroot
from pants_test.pants_run_integration_test import PantsRunIntegrationTest


class ProtobufIntegrationTest(PantsRunIntegrationTest):
  def test_bundle_protobuf_normal(self):
    pants_run = self.run_pants(
        ['goal', 'bundle', 'examples/src/java/com/pants/examples/protobuf:protobuf-example',
         '--bundle-deployjar', '--print-exception-stacktrace',])
    self.assertEquals(pants_run.returncode, self.PANTS_SUCCESS_CODE,
                      "goal bundle run expected success, got {0}\n"
                      "got stderr:\n{1}\n"
                      "got stdout:\n{2}\n".format(pants_run.returncode,
                                                  pants_run.stderr_data,
                                                  pants_run.stdout_data))
    out_path = os.path.join(get_buildroot(), 'dist', 'protobuf-example-bundle')
    java_run = subprocess.Popen(['java', '-cp', 'protobuf-example.jar',
                                 'com.pants.examples.protobuf.ExampleProtobuf'],
                                stdout=subprocess.PIPE,
                                cwd=out_path)
    java_retcode = java_run.wait()
    java_out = java_run.stdout.read()
    self.assertEquals(java_retcode, 0)
    self.assertTrue("parsec" in java_out)

  def test_bundle_protobuf_imports(self):
    pants_run = self.run_pants(
        ['goal', 'bundle', 'examples/src/java/com/pants/examples/protobuf:protobuf-imports-example',
         '--bundle-deployjar', '--print-exception-stacktrace',])
    self.assertEquals(pants_run.returncode, self.PANTS_SUCCESS_CODE,
                      "goal bundle run expected success, got {0}\n"
                      "got stderr:\n{1}\n"
                      "got stdout:\n{2}\n".format(pants_run.returncode,
                                                  pants_run.stderr_data,
                                                  pants_run.stdout_data))
    out_path = os.path.join(get_buildroot(), 'dist', 'protobuf-imports-example-bundle')
    java_run = subprocess.Popen(['java', '-cp', 'protobuf-imports-example.jar',
                                 'com.pants.examples.protobuf.imports.ExampleProtobufImports'],
                                stdout=subprocess.PIPE,
                                cwd=out_path)
    java_retcode = java_run.wait()
    java_out = java_run.stdout.read()
    self.assertEquals(java_retcode, 0)
    self.assertTrue("very test" in java_out)

  def test_source_ordering(self):
    pants_run = self.run_pants([
        'goal', 'gen', 'testprojects/src/java/com/pants/testproject/proto-ordering', '--level=debug',
         '--print-exception-stacktrace', '--gen-protoc-lang=java',
    ])
    self.assertEquals(pants_run.returncode, self.PANTS_SUCCESS_CODE,
                      "goal bundle run expected success, got {0}\n"
                      "got stderr:\n{1}\n"
                      "got stdout:\n{2}\n".format(pants_run.returncode,
                                                  pants_run.stderr_data,
                                                  pants_run.stdout_data))
    def find_protoc_blocks(lines):
      block = []
      for line in lines:
        if block:
          if line.strip():
            block.append(line.strip())
          else:
            yield block
            block = []
          continue
        if re.search(r'Executing: .*?\bprotoc', line):
          block.append(line)

    # Scraping debug statements for protoc compilation. Notably, debugs are in stderr, not stdout.
    all_blocks = list(find_protoc_blocks(pants_run.stderr_data.split('\n')))
    self.assertEquals(len(all_blocks), 1,
        'Expected there to be exactly one protoc compilation group! (Were {count}.)\n{out}'
        .format(count=len(all_blocks), out=pants_run.stderr_data))

    block = all_blocks[0]
    seen_extracted = False
    last_proto = -1
    for line in block:
      # Make sure import bases appear after the bases for actual sources.
      if line.startswith('--proto_path='):
        if re.search(r'\bextracted\b', line):
          seen_extracted = True
        else:
          self.assertFalse(seen_extracted,
              'Local protoc bases must be ordered before imported bases!')
        continue
      # Check to make sure, eg, testproto4.proto never preceedes testproto2.proto.
      protofile = re.search(r'\d+[.]proto$', line)
      if protofile:
        protofile = protofile.group()
        number = int(protofile[:protofile.find('.')])
        self.assertTrue(number > last_proto, '{proto} succeeded proto #{number}!'.format(
            proto=line, number=last_proto))
        last_proto = number
    self.assertEquals(last_proto, 6, 'Not all protos were seen!')
