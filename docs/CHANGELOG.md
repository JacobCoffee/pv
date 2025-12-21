# Changelog

All notable changes to this project will be documented in this file.

## [1.1.2](https://github.com/JacobCoffee/pv/compare/v1.1.1..v1.1.2) - 2025-12-21


### Documentation


- regenerate changelog for v1.1.1 - ([3fbc9d8](https://github.com/JacobCoffee/pv/commit/3fbc9d8d76c3bdc08272867c6ee921749ac1836f)) - github-actions[bot]

- add changelog to navigation - ([a6c164c](https://github.com/JacobCoffee/pv/commit/a6c164c1f661f3c1a1bfd41809fee1166730bda7)) - Jacob Coffee


### Miscellaneous Chores


- bump version to 1.1.2 - ([39d8acc](https://github.com/JacobCoffee/pv/commit/39d8acc80f88ddf4070e8f7a3ed3c75d54eb8f93)) - Jacob Coffee
## [1.1.1](https://github.com/JacobCoffee/pv/compare/v1.1.0..v1.1.1) - 2025-12-21


### Bug Fixes


- **(cd)** checkout main branch for changelog workflow - ([b262a39](https://github.com/JacobCoffee/pv/commit/b262a390e54a25adb77f02e24aecc0eb3f55c442)) - Jacob Coffee

### Miscellaneous Chores


- bump version to 1.1.1 - ([1b7f829](https://github.com/JacobCoffee/pv/commit/1b7f8298b67ca73f6245d7dbbb9f40d56f43138d)) - Jacob Coffee
## [1.1.0](https://github.com/JacobCoffee/pv/compare/v1.0.1..v1.1.0) - 2025-12-21


### Bug Fixes


- **(ci)** checkout main branch in changelog workflow - ([9bd7e56](https://github.com/JacobCoffee/pv/commit/9bd7e5692fa6d40d73d4ae76ed88bc1183b330c7)) - Jacob Coffee
- **(ci)** explicitly set remote URL with token in changelog workflow - ([255742c](https://github.com/JacobCoffee/pv/commit/255742ce76dc3e6763e185563671c793378fae0e)) - Jacob Coffee
- **(ci)** use --current instead of --unreleased for release notes - ([c72eaa7](https://github.com/JacobCoffee/pv/commit/c72eaa799f726f383664d224b839cf98bf8ce10c)) - Jacob Coffee
- move return to else block per TRY300 lint rule - ([9d51c07](https://github.com/JacobCoffee/pv/commit/9d51c0731eac1ddba372e24566d9aed3ba73240f)) - Jacob Coffee


### Documentation


- regenerate changelog for v1.0.1 - ([e305677](https://github.com/JacobCoffee/pv/commit/e3056771d5d9a42fe44250bd377021591c64ab1f)) - github-actions[bot]

- overhaul documentation and add examples - ([39cd895](https://github.com/JacobCoffee/pv/commit/39cd89536dccdc50d4dc66fed39462f52d458934)) - Jacob Coffee


### Features


- add bugs/deferred display commands and smart task creation - ([121f2b4](https://github.com/JacobCoffee/pv/commit/121f2b40eb305f0b6bd7e5c791d98472f700018c)) - Jacob Coffee


### Miscellaneous Chores


- bump version to 1.1.0 - ([c60b717](https://github.com/JacobCoffee/pv/commit/c60b717bd3698a2abeaf800dc66904d67cf1f852)) - Jacob Coffee


### Revert


- undo cd.yml workflow changes - ([173e2ab](https://github.com/JacobCoffee/pv/commit/173e2abca501f8045d5ffedf44db6af9ee726ddf)) - Jacob Coffee


### Tests


- add tests for special phase creation and achieve 100% coverage - ([2d97ed9](https://github.com/JacobCoffee/pv/commit/2d97ed94d9508b2b216b49adfe9dedbcdedd37c7)) - Jacob Coffee
## [1.0.1](https://github.com/JacobCoffee/pv/compare/v1.0.0..v1.0.1) - 2025-12-21


### Bug Fixes


- resolve remaining lint errors and bump to v1.0.1 - ([4959105](https://github.com/JacobCoffee/pv/commit/4959105f4a478cdd928b5e9c2c56ee61ac713564)) - Jacob Coffee
## [1.0.0](https://github.com/JacobCoffee/pv/compare/v0.2.0..v1.0.0) - 2025-12-21


### Bug Fixes


- resolve lint errors in test files - ([fea4743](https://github.com/JacobCoffee/pv/commit/fea47436c5b448dd5c718a85e3c322dec14f2369)) - Jacob Coffee


### Features


- add NO_COLOR and FORCE_COLOR environment variable support - ([6a9cfc3](https://github.com/JacobCoffee/pv/commit/6a9cfc3ef2b94fe357587bbd5f5d2d2d1987ed98)) - Jacob Coffee

- add block and skip command shortcuts - ([e2d9b16](https://github.com/JacobCoffee/pv/commit/e2d9b164c51ca61126b52c8e2870cabf662a5817)) - Jacob Coffee

- add defer command to move tasks to deferred phase - ([85fbd92](https://github.com/JacobCoffee/pv/commit/85fbd92e9049c9cb7a0d777a0e19137d2b37e764)) - Jacob Coffee

- add --quiet / -q flag to suppress edit command output - ([036a936](https://github.com/JacobCoffee/pv/commit/036a93621e284b899186217ee97a6bce5dfbbedb)) - Jacob Coffee

- improve error messages with actionable suggestions - ([43fc3bd](https://github.com/JacobCoffee/pv/commit/43fc3bdefcf0d3bbd78f93e3de93f1706eeca890)) - Jacob Coffee

- add --all / -a flag to 'pv last' command - ([56f081d](https://github.com/JacobCoffee/pv/commit/56f081d695e2ebfc870da9476ac932d76a7006d6)) - Jacob Coffee

- support partial task ID matching - ([04b0ca1](https://github.com/JacobCoffee/pv/commit/04b0ca163617360aa49b4f22ac198cb64e837d89)) - Jacob Coffee

- add 'pv summary' command for lightweight JSON export - ([3a9b917](https://github.com/JacobCoffee/pv/commit/3a9b917b9b56d0a9c83c1dc82ef4f6aa220c459a)) - Jacob Coffee

- add --dry-run / -d flag for edit commands - ([08f8b11](https://github.com/JacobCoffee/pv/commit/08f8b115b2f4bcb76abe77792bc5aae3b1dcec5c)) - Jacob Coffee

- add optional priority field to task schema - ([b983034](https://github.com/JacobCoffee/pv/commit/b983034daea87371750542ea2e5b8c5d09ec939f)) - Jacob Coffee

- add optional estimated_minutes field to task schema - ([3db0f1a](https://github.com/JacobCoffee/pv/commit/3db0f1a1a4f7f3851f7352253d144c7dc8ccb5a2)) - Jacob Coffee

- replace fixed agent_type enum with flexible validation - ([3f36844](https://github.com/JacobCoffee/pv/commit/3f3684447dcfb9b324fde6849482e7c3f26da223)) - Jacob Coffee

- add schema_version field to meta for migration support - ([9cf4e39](https://github.com/JacobCoffee/pv/commit/9cf4e394ebe3896c7bd995bfb96348490f02c370)) - Jacob Coffee

- improve depends_on validation in schema - ([ac6f54a](https://github.com/JacobCoffee/pv/commit/ac6f54a1981b817e8b11fa4ff64e93eb66c9e5fe)) - Jacob Coffee

- complete remaining tasks (1.1.6, 4.1.1, 99.1.1, 99.1.2) - ([dc37d3e](https://github.com/JacobCoffee/pv/commit/dc37d3e51c952b64e2f89a7ebf2063c80770ea40)) - Jacob Coffee


### Miscellaneous Chores


- trigger CI - ([912c1af](https://github.com/JacobCoffee/pv/commit/912c1afbba3c68ade5af0913b5f10508a0ed18ad)) - Jacob Coffee

- bump version to 1.0.0 - ([44d77f8](https://github.com/JacobCoffee/pv/commit/44d77f8b844be2741cb5c4a1ec0b47318d922273)) - Jacob Coffee


### Performance


- optimize dependency check in get_next_task() - ([3fcd56a](https://github.com/JacobCoffee/pv/commit/3fcd56acec5a467a637a2038af1900fc7a1d9ff8)) - Jacob Coffee


### Refactoring


- remove get_status_icon, derive VALID_STATUSES from ICONS - ([342e337](https://github.com/JacobCoffee/pv/commit/342e337ae9ad21765830021a05994034a9aaed0a)) - Jacob Coffee


### Tests


- add concurrent file access and race condition tests - ([940481c](https://github.com/JacobCoffee/pv/commit/940481cf38a657d50bac985811d3194ac9495864)) - Jacob Coffee

- add phase 3 test hardening (3.1.2, 3.1.3, 3.1.4) - ([d11c681](https://github.com/JacobCoffee/pv/commit/d11c6815244d40c49b7c3d40cca9efd071738fc0)) - Jacob Coffee


### Ci


- use git-cliff for release notes, fix changelog token - ([a25caf9](https://github.com/JacobCoffee/pv/commit/a25caf956d74a381d8627fc7de51ed90adcb4785)) - Jacob Coffee

- changelog workflow creates PR instead of direct push - ([d8f92a3](https://github.com/JacobCoffee/pv/commit/d8f92a3b6cd0f315dffee2fa647197d549ddac81)) - Jacob Coffee

- revert changelog to direct push with PAT - ([61e52c4](https://github.com/JacobCoffee/pv/commit/61e52c46348cd570e3a26a2a96b7f1dfa1c1177a)) - Jacob Coffee

- persist credentials for changelog push - ([db7db7f](https://github.com/JacobCoffee/pv/commit/db7db7fb8d1af177102bf06d4933a9027df8f261)) - Jacob Coffee
## [0.2.0] - 2025-12-21


### Bug Fixes


- use argparse, fix f-string syntax, Python 3.14 only - ([6990303](https://github.com/JacobCoffee/pv/commit/6990303f1fd94c88c3023c95e34f495c375b3d77)) - Jacob Coffee

- move find_task import to top-level - ([e83c255](https://github.com/JacobCoffee/pv/commit/e83c2554ab7e42bcf892f65ed5b47820ccb58929)) - Jacob Coffee

- rename package to plan-view - ([1c8ced7](https://github.com/JacobCoffee/pv/commit/1c8ced77478dc03bd7f3c38c43ea512f224bebcb)) - Jacob Coffee


### Documentation


- add Sphinx documentation with Shibuya theme - ([55d28b6](https://github.com/JacobCoffee/pv/commit/55d28b69e534df58a74faca0e23a116e6b1bb4c5)) - Jacob Coffee


### Features


- initial pv-tool implementation - ([fd2416e](https://github.com/JacobCoffee/pv/commit/fd2416e76e667c7eaca4fe4cd9a68f2047a190a7)) - Jacob Coffee

- add edit commands (init, add-phase, add-task, set, done, start, rm) - ([2b150f9](https://github.com/JacobCoffee/pv/commit/2b150f9042b5b703dd8ccd123c62790c5cf2c154)) - Jacob Coffee

- add jsonschema validation with bundled schema - ([841aa0f](https://github.com/JacobCoffee/pv/commit/841aa0f48340ef74c94f4ffe2057f008757ef71e)) - Jacob Coffee

- add shorthand aliases (c, n, p, v) - ([869adab](https://github.com/JacobCoffee/pv/commit/869adab2f5d299a71505cc37be2ce79bd25bcfe5)) - Jacob Coffee

- add help command - ([e7d231b](https://github.com/JacobCoffee/pv/commit/e7d231be6ab6c287ec88ee39850fa5de0ec0c284)) - Jacob Coffee


### Miscellaneous Chores


- **(deps)** bump the actions group with 7 updates (#1) - ([6dfb014](https://github.com/JacobCoffee/pv/commit/6dfb014b75923cb6404cd4265a1e22a162ae0f15)) - dependabot[bot]
- **(release)** v0.2.0 - ([c1c5c94](https://github.com/JacobCoffee/pv/commit/c1c5c945286e544c76bba46fe01fffb123291984)) - Jacob Coffee
- remove duplicate schema (bundled in src/pv_tool/) - ([063c3ca](https://github.com/JacobCoffee/pv/commit/063c3ca324e18e7e736c22e39cb495a6aff82e35)) - Jacob Coffee

- switch to uv_build backend, target Python 3.14 - ([5c19def](https://github.com/JacobCoffee/pv/commit/5c19def932c40efdde3a8a77e9c7d878d4f5a18a)) - Jacob Coffee

- enable ALL ruff rules with sensible ignores - ([08ccbe2](https://github.com/JacobCoffee/pv/commit/08ccbe2a0056408b2127d916b7c6de63dff14e60)) - Jacob Coffee

- add Makefile with lint/fmt/ci targets - ([b9caae6](https://github.com/JacobCoffee/pv/commit/b9caae64b2d1e4c71a7d194c45d374858d042d8c)) - Jacob Coffee

- add Google-style docstrings, enable type annotation linting - ([beaf5a8](https://github.com/JacobCoffee/pv/commit/beaf5a855704472aed9b4f5bc455e3c5839fa1d5)) - Jacob Coffee


### Refactoring


- [**breaking**] rename package from pv-tool to plan-view - ([b614a7a](https://github.com/JacobCoffee/pv/commit/b614a7a56e60c28765b763b0e602b66aad828cdf)) - Jacob Coffee


### Tests


- add comprehensive test suite with 100% coverage - ([999cbd8](https://github.com/JacobCoffee/pv/commit/999cbd81429310f486fb230cab2774f11a46636e)) - Jacob Coffee
---
*pv-tool Changelog*
