Changelog
=========


0.10.3 (2019-11-07)
-----------------------------
- Checking manifest with pre-commit (#55) [Miroslav Shubernetskiy]


0.10.2 (2019-10-31)
-------------------
- Accounting for all expandable fields (#54) [Miroslav Shubernetskiy]


0.10.1 (2019-10-30)
-------------------
- Expandable serializer uses selectinload for *tomany (#53) [Miroslav
  Shubernetskiy]


0.10.0 (2019-08-31)
-------------------
- Drop py2 support (#51) [Serkan Hosca]
- Pytest and black configs (#49) [Serkan Hosca]
- Add SearchFilter (#47) [Serkan Hosca]
- Use python/black (#46) [Serkan Hosca]


0.9.0 (2019-06-28)
------------------
- Drop enumfield and update importanize config (#45) [Serkan Hosca]


0.8.3 (2019-06-27)
------------------
- Fix module test runner target (#44) [Serkan Hosca]
- Switching to tox-travis and tox matrix (#43) [Miroslav Shubernetskiy]
- Run tests with pg (#42) [Serkan Hosca]
- Update pre-commit (#41) [Serkan Hosca]


0.8.2 (2019-02-11)
------------------
- Fix Unicode type column mapping (#40) [Serkan Hosca]


0.8.1 (2019-01-08)
------------------
- Allowing to overwrite fields and exclude on serializer init (#38)
  [Miroslav Shubernetskiy]


0.8.0 (2019-01-05)
------------------
- Grab composite meta info from parent model (#37) [Serkan Hosca]
- Coersion fixes from django-sorcery (#36) [Serkan Hosca]


0.7.20 (2018-12-13)
-------------------
- Fix enum field custom kwargs (#35) [Serkan Hosca]


0.7.19 (2018-11-28)
-------------------
- Pop widget from args (#34) [Serkan Hosca]


0.7.18 (2018-11-26)
-------------------
- Stop using deprecated functions (#33) [Serkan Hosca]


0.7.17 (2018-11-24)
-------------------
- Fix enum field and make it more generic (#32) [Serkan Hosca]


0.7.16 (2018-11-19)
-------------------
- Fix composite source (#31) [Serkan Hosca]
- Remove pipenv (#30) [Serkan Hosca]


0.7.15 (2018-11-14)
-------------------
- Handling ValidationError in update on set attribute (#28) [Miroslav
  Shubernetskiy]





- Bump pre-commit check versions (#27) [Serkan Hosca]


0.7.14 (2018-11-07)
-------------------
- Fixing typo referencing session which does not exist (#26) [Miroslav
  Shubernetskiy]







0.7.13 (2018-11-06)
-------------------
- Adding query_model hook (#24) [Miroslav Shubernetskiy]


0.7.12 (2018-11-05)
-------------------
- Remove url default field from ModelSerializer (#25) [Serkan Hosca]
- Update lock. [Serkan Hosca]


0.7.11 (2018-11-01)
-------------------
- Hook for how model is created (#22) [Miroslav Shubernetskiy]
- Fix serializer tests (#23) [Serkan Hosca]
- Relock (#20) [Serkan Hosca]
- Drop py3.5 build. [Serkan Hosca]


0.7.10 (2018-08-13)
-------------------
- Partial by pk (#19) [Miroslav Shubernetskiy]







- Allowing to overwrite extra_kwargs in Serializer.__init__ (#18)
  [Miroslav Shubernetskiy]


0.7.9 (2018-08-08)
------------------
- ExpandableModelSerializer (#17) [Miroslav Shubernetskiy]























- Fixing saving serializer with source=* (#16) [Miroslav Shubernetskiy]







0.7.5 (2018-07-24)
------------------
- Correctly removing composite when validated data is None (#15)
  [Miroslav Shubernetskiy]


0.7.4 (2018-07-20)
------------------
- Fixing enum field choices (#14) [Miroslav Shubernetskiy]


0.7.3 (2018-07-16)
------------------
- Fixing updating model when field.field_name != field.source (#13)
  [Miroslav Shubernetskiy]





- Add nested update test (#12) [Serkan Hosca]


0.7.2 (2018-06-28)
------------------
- Merge pull request #10 from shosca/composite-labels. [Serkan Hosca]
- Fixing uri field for multiple pk models. fixed tests. [Miroslav
  Shubernetskiy]
- Honoring lookup_field iin querying model in generics.py when single
  pk. [Miroslav Shubernetskiy]
- Normalizing django validation errors in apis. [Miroslav Shubernetskiy]
- Fixing composite serializer field labels to use compose fields vs
  column names. [Miroslav Shubernetskiy]


0.7.1 (2018-06-26)
------------------
- Merge pull request #11 from shosca/relation-null-set. [Serkan Hosca]
- Fix many-to-one or one-to-one relation null set. [Serkan Hosca]


0.7.0 (2018-06-10)
------------------
- Merge pull request #9 from shosca/use-sorcery. [Serkan Hosca]
- Add sorcery as dependency. [Serkan Hosca]


0.6.2 (2018-02-23)
------------------
- Merge pull request #8 from shosca/packaging. [Serkan Hosca]
- Fix packaging. [Serkan Hosca]


0.6.1 (2018-01-08)
------------------

Fix
~~~
- Adjust build_nested_field signature. [Serkan Hosca]

Other
~~~~~
- Version 0.6.1. [Serkan Hosca]
- Merge pull request #7 from shosca/relation-info. [Serkan Hosca]


0.6.0 (2018-01-05)
------------------
- Version 0.6.0. [Serkan Hosca]
- Merge pull request #5 from shosca/build-field-signature. [Serkan
  Hosca]
- Add model_class to build_field. [Serkan Hosca]


0.5.6 (2017-12-21)
------------------
- Merge pull request #3 from nickswiss/enum-mapping. [Serkan Hosca]
- Adding enums to field mapping dict. [Nick Arnold]


0.5.5 (2017-11-02)
------------------

Fix
~~~
- Declared fields. [Serkan Hosca]

Other
~~~~~
- 0.5.5. [Serkan Hosca]
- Merge pull request #2 from shosca/fix-declared-fields. [Serkan Hosca]


0.5.4 (2017-10-23)
------------------

Fix
~~~
- Super for py2. [Serkan Hosca]

Refactor
~~~~~~~~
- Separate out session flush. [Serkan Hosca]


0.5.2 (2017-10-21)
------------------

Fix
~~~
- Deepcopy composite and model serializers. [Serkan Hosca]


0.5.1 (2017-10-04)
------------------

Refactor
~~~~~~~~
- Handle session passing around. [Serkan Hosca]

Other
~~~~~
- Merge pull request #1 from shosca/session-distribution. [Serkan Hosca]


0.5.0 (2017-10-03)
------------------

Refactor
~~~~~~~~
- Make enums use values instead of names. [Serkan Hosca]
- Use relationship mapper to get target model class. [Serkan Hosca]

Other
~~~~~
- Add LICENSE. [Serkan Hosca]
- Pipfile lock. [Serkan Hosca]


0.4.3 (2017-07-06)
------------------

Fix
~~~
- Allow_null is not allowed in boolean fields. [Serkan Hosca]


0.4.2 (2017-07-02)
------------------

Fix
~~~
- Handle composite pks when one pk is None. [Serkan Hosca]


0.4.1 (2017-07-01)
------------------

Fix
~~~
- Nested model primary key field generation. [Serkan Hosca]

Other
~~~~~
- Fix readme. [Serkan Hosca]


0.4.0 (2017-06-28)
------------------

Fix
~~~
- Field label generation. [Serkan Hosca]

Refactor
~~~~~~~~
- Lots of minor pylint and pycharm linter fixes. [Serkan Hosca]

Other
~~~~~
- Update gitchangelog.rc. [Serkan Hosca]


0.3.5 (2017-06-18)
------------------

Fix
~~~
- Increase coverage. [Serkan Hosca]

Refactor
~~~~~~~~
- Dedup update attribute logic. [Serkan Hosca]
- Run pre-commit as part of build. [Serkan Hosca]


0.3.4 (2017-06-14)
------------------

Refactor
~~~~~~~~
- Better route name handling and nullable boolean field tests. [Serkan
  Hosca]

Documentation
~~~~~~~~~~~~~
- Update gitchangelog config. [Serkan Hosca]


0.3.3 (2017-06-13)
------------------

Fix
~~~
- Add pipenv for setup. [Serkan Hosca]

Documentation
~~~~~~~~~~~~~
- Fix versioning. [Serkan Hosca]


0.3.2 (2017-06-13)
------------------

Fix
~~~
- Stop passing around is_nested and fix autoincrement value check.
  [Serkan Hosca]


0.3.1 (2017-06-11)
------------------
- Delete tests and coverall config. [Serkan Hosca]


0.3.0 (2017-06-11)
------------------

Fix
~~~
- Nested list serializer flags. [Serkan Hosca]
- Generic destroy with sqlalchemy. [Serkan Hosca]
- Handle autoincrement and nested update with existing instance. [Serkan
  Hosca]

Refactor
~~~~~~~~
- Model_info changes and added docstrings. [Serkan Hosca]

Other
~~~~~
- Initial doc setup. [Serkan Hosca]


0.2.1 (2017-06-10)
------------------
- Initial doc setup. [Serkan Hosca]


0.2.0 (2017-06-10)
------------------
- Refactor field mapping and object fetching and more tests. [Serkan
  Hosca]


0.1.4 (2017-06-09)
------------------
- Respect allow_null. [Serkan Hosca]


0.1.2 (2017-06-08)
------------------
- Mark all columns read only when allow_nested_updates is false. [Serkan
  Hosca]


0.1.1 (2017-06-07)
------------------
- Fix composite serializer. [Serkan Hosca]


0.1.0 (2017-06-06)
------------------
- Add more tests and generic api fixes. [Serkan Hosca]


0.0.6 (2017-06-05)
------------------
- Add missing dep and add pypi badge. [Serkan Hosca]
- Add more tests for composite routes. [Serkan Hosca]


0.0.5 (2017-06-05)
------------------
- Add route tests. [Serkan Hosca]


0.0.4 (2017-06-05)
------------------
- Add pre-commit. [Serkan Hosca]
- Move GenericAPIView. [Serkan Hosca]
- Fix Readme. [Serkan Hosca]


0.0.2 (2017-06-02)
------------------
- Fix setup publish and make clean. [Serkan Hosca]
- Added viewsets and version bump. [Serkan Hosca]
- Update readme. [Serkan Hosca]


0.0.1 (2017-06-02)
------------------
- Fix readme. [Serkan Hosca]
- Added initial readme. [Serkan Hosca]
- Add travis. [Serkan Hosca]
- Initial commit. [Serkan Hosca]


