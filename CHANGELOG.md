# Changelog

## [1.0.1](https://github.com/raci-sh/raci-spec/compare/v1.0.0...v1.0.1) (2026-11-22)


### Bug Fixes

* **spec:** allow at most one result per constraint in an event ([310795b](https://github.com/raci-sh/raci-spec/commit/310795b4ad776d0902747865d3aa8785163cf1c6))
* **spec:** close bypasses of conflict pairs, split the revert rule ([ba8ce8f](https://github.com/raci-sh/raci-spec/commit/ba8ce8f5e1df69b74148e0a359b50787a58f709f))
* **spec:** fail closed on unreplayable logs, pin the exact sh.raci source ([098a1a5](https://github.com/raci-sh/raci-spec/commit/098a1a56021fb81a6ce9f01e9008a52968a439bc))
* **spec:** make event constraints an object keyed by name ([4b6efa3](https://github.com/raci-sh/raci-spec/commit/4b6efa3b89674dc250e1ac7df80ae621b1bc487b))
* **spec:** qualify resource references by realm, define deletion ([3d2b188](https://github.com/raci-sh/raci-spec/commit/3d2b188ac48d011b1a44b3902f8a71ed9788da53))
* **spec:** reject trailing newlines and correct the seq truncation claim ([59c763e](https://github.com/raci-sh/raci-spec/commit/59c763e5226fc2d020923735e069889efcba4f8e))
* **spec:** replace imported rules on pin, fail closed until doctor revert ([fa282aa](https://github.com/raci-sh/raci-spec/commit/fa282aab68eae0a9f66bb5e0433c97517ce5be79))
* **spec:** reset new-rule revisions, validate ts ranges, resolve schema refs ([0ddbe8f](https://github.com/raci-sh/raci-spec/commit/0ddbe8f334c03cb0b526b7adbf298587cfd41271))
* **spec:** support separation of duties and selectors in version 1 ([914b40b](https://github.com/raci-sh/raci-spec/commit/914b40b0e1c379cf22dd41fd7efa5a1b85a3e25b))
* **spec:** version events, pin content digests, close schema gaps ([8b86963](https://github.com/raci-sh/raci-spec/commit/8b86963fcc8abeb877f4a850f0b3a2e9e94e8c68))


### Documentation

* **spec:** pin the raci/1 wire format and sh.raci versioning ([e40c3a1](https://github.com/raci-sh/raci-spec/commit/e40c3a147ecdeefa303d3fda5f4ab6ddaaaab5c9))

## 1.0.0 (2026-11-21)


### Features

* **rules:** add RACIDINF with a minimal default inference rule ([02b21f1](https://github.com/raci-sh/raci-spec/commit/02b21f10600ea5bcc1802176dd5cd92f19db5793))
* **rules:** add RACIDINF with a minimal default inference rule ([37063ac](https://github.com/raci-sh/raci-spec/commit/37063ac6b22de2bd46c6cc67512fa9991bc7d49e))
* **rules:** add RACIDMGT with the default rule-management rules ([8e4d060](https://github.com/raci-sh/raci-spec/commit/8e4d0609697d1dc5cd8aea9b4c0349169ac87510))
* **rules:** add RACIDMGT with the default rule-management rules ([4cf6841](https://github.com/raci-sh/raci-spec/commit/4cf68416ab7fc14df011d82a6056ab187ec4ef3e))
* **rules:** adopt the structured note type from core 1.23.0 ([c73d6d5](https://github.com/raci-sh/raci-spec/commit/c73d6d5331f33ffa7699ead39646756619707003))
* **rules:** adopt the structured note type from core 1.23.0 ([5dd261b](https://github.com/raci-sh/raci-spec/commit/5dd261bf4fae6c70601cea9cf0d0f6f992ce79db))


### Bug Fixes

* **ci:** reject unsupported payload formats explicitly ([18d399f](https://github.com/raci-sh/raci-spec/commit/18d399f01b3dc797e48d27aea8aab6d7e4fb8f05))
* **rules:** bump the retyped note revisions and the RACIDCNS version ([f7a916d](https://github.com/raci-sh/raci-spec/commit/f7a916d67038c4cf28a729e94b4826ea1bb63722))
* **rules:** define inference activity semantics and restrict the wildcard ([b173d86](https://github.com/raci-sh/raci-spec/commit/b173d8607378b27184193407817c98cd1990d81d))
* **rules:** drop the RACIDMGT issuer defaults that conflict with RACIDINF-001 ([aa3e94d](https://github.com/raci-sh/raci-spec/commit/aa3e94ddf670d0812c7ec1c842a099c1a320da38))
* **rules:** give RACIDMGT a structured activity-set source ([9b1a769](https://github.com/raci-sh/raci-spec/commit/9b1a7696436920b6d1def7696da6e7870b18a1a5))
* **spec:** tie requires to separation-of-duties and keep it out of presets ([25f0c66](https://github.com/raci-sh/raci-spec/commit/25f0c66d17e6bc7d0826966a894d5fdcdbe24b77))


### Documentation

* add audit log, separation of duties and SteerSpec mapping to SPEC ([d210480](https://github.com/raci-sh/raci-spec/commit/d210480c9c1f7dc04fe2fe0308a1d2be6d8cb03f))
* add draft SPEC.md ([0b7f216](https://github.com/raci-sh/raci-spec/commit/0b7f216cb59c4d0551d392d09ac529fa7328fd14))
* add draft SPEC.md ([39efb8b](https://github.com/raci-sh/raci-spec/commit/39efb8beab1cc85b8a96b1b503c97557baff9245))
* add RACIAUD, RACIFILE and RACIMGT entities to the sh.raci realm ([4e15cff](https://github.com/raci-sh/raci-spec/commit/4e15cffa7750a77093619c7da5504cffe85c49c6))
* add RACIAUD, RACIFILE and RACIMGT entities to the sh.raci realm ([9e3373e](https://github.com/raci-sh/raci-spec/commit/9e3373edd16a98e19eb47b38ffb624d145060466))
* add RACIINH and RACIINF entities to the sh.raci realm ([52db291](https://github.com/raci-sh/raci-spec/commit/52db2918f213237a46b83fa62c8a7afcd254c712))
* add RACIINH and RACIINF entities to the sh.raci realm ([b8b9cd7](https://github.com/raci-sh/raci-spec/commit/b8b9cd79cc310688b67d0110228b3be68d737e82))
* add resource model, hierarchy mapping and replay rules ([747fd5a](https://github.com/raci-sh/raci-spec/commit/747fd5a23b12f3a6f7d66589551bca1cbee66cf6))
* add sh.raci SteerSpec realm (RACI, RACICNS, RACIDCNS) ([d99b81f](https://github.com/raci-sh/raci-spec/commit/d99b81f898d23a75ce63b1551d1c2b9cfdee057d))
* add sh.raci SteerSpec realm with RACI, RACICNS and RACIDCNS ([5173334](https://github.com/raci-sh/raci-spec/commit/5173334b2b74de09ebcf09b8b01dfba64db6bce0))
* address review on SoD scope, inference chains and audit events ([9b64ff7](https://github.com/raci-sh/raci-spec/commit/9b64ff775bca0680a8f5bb06e093d665c6a9edf8))
* address review on the .raci format ([94bc676](https://github.com/raci-sh/raci-spec/commit/94bc67686b5c14bcad6e1546402025c598b5983e))
* bind map and strip to the source type, add selector, restrict add-issuer ([85c4d4d](https://github.com/raci-sh/raci-spec/commit/85c4d4d8ca4cfe6a48b0047441dce1a382507a77))
* define hash verification, override strength and rule bootstrap ([8ee8827](https://github.com/raci-sh/raci-spec/commit/8ee882735d1c2df690e7dd7ea0533ccd04c49896))
* define the .raci file format and verification report ([61f6849](https://github.com/raci-sh/raci-spec/commit/61f68499a7c5bf92c84defce55635a526da6a205))
* define the .raci file format and verification report ([0a11be7](https://github.com/raci-sh/raci-spec/commit/0a11be75e9016ad9f772be7ff4bcbeabef491ed1))
* define transaction, no-match and rule source semantics ([9a2abb9](https://github.com/raci-sh/raci-spec/commit/9a2abb9471c94a8c2da7e39155dd621a3dabb972))
* fix pin field name, digest encoding and path-free view ([821ff2a](https://github.com/raci-sh/raci-spec/commit/821ff2a5a0ef450da72e9470cc1cf81e715e8e95))
* fix RACIINF revisions and add activity to delta composition ([21630b6](https://github.com/raci-sh/raci-spec/commit/21630b6cfd02eafe91f44bb0dfd34974fc67473c))
* give strip a source type like map ([a01b5fa](https://github.com/raci-sh/raci-spec/commit/a01b5faebd74b2b0509223172a83501b4bebea33))
* limit pin-update rule events to structured rules ([9a04e62](https://github.com/raci-sh/raci-spec/commit/9a04e62da04023c469eca9818857d3c9639f5e27))
* limit rule events and unrecorded checks to structured sources ([791cfbf](https://github.com/raci-sh/raci-spec/commit/791cfbf4da7aeab173c44e25e755c13cea59d579))
* name the missing rule event explicitly in the unrecorded check ([e8ce775](https://github.com/raci-sh/raci-spec/commit/e8ce77580a0edfbd4020cfa9106a4533f55ea642))
* revalidate descendants and compose rule deltas ([9f86903](https://github.com/raci-sh/raci-spec/commit/9f869039fc26c9922e7d524384ea0b4ffbb948fc))
* scope rule events to structured rules and fix reject semantics ([5c61cf5](https://github.com/raci-sh/raci-spec/commit/5c61cf599513cd70ed1aa066613899fdf5134acb))
* scope the latest rule event lookup by rule id ([d6385ea](https://github.com/raci-sh/raci-spec/commit/d6385ead6b63b482c10800b8e634f853d63e3978))
* **spec:** draft the raci/1 structured payload format ([5d1f980](https://github.com/raci-sh/raci-spec/commit/5d1f9803f86944078881c10102fa64109084e2a4))
* **spec:** draft the raci/1 structured payload format ([5210b26](https://github.com/raci-sh/raci-spec/commit/5210b26894701fe1f55419f02e41f55010d6a5a1))
* tie trigger types to entry operations ([f593b9d](https://github.com/raci-sh/raci-spec/commit/f593b9da2db8afafd63501e6c4e8d0bb43357347))
