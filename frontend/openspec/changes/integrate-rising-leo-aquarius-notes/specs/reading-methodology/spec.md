## ADDED Requirements

### Requirement: The system SHALL support structured teaching-note content

The product SHALL store long-form astrology teaching notes in structured configuration objects instead of embedding raw prose directly inside components.

#### Scenario: Rising-sign note set is normalized for rendering

- **WHEN** the team integrates a themed teaching note such as `0613 占星笔记`
- **THEN** the note is split into reusable blocks for primer content, rising-sign guides, and planet-specific lenses
- **AND** each block can separately provide user-facing summary text and astrologer-facing note text

#### Scenario: The content model can grow beyond Leo and Aquarius

- **WHEN** future rising-sign teaching notes are added
- **THEN** the new sign can be appended by data entry
- **AND** existing rendering components do not require structural rewrites

### Requirement: The system SHALL expose relationship-depth primer content in methodology surfaces

The product SHALL explain the difference between ascendant, sun, and moon visibility layers in the methodology surfaces.

#### Scenario: User opens a methodology entry point

- **WHEN** a user views the homepage methodology area or the report reading-method panel
- **THEN** the user can see a compact explanation that ascendant corresponds to first impression, sun to familiar identity, and moon to intimate emotional self
- **AND** the content is presented as a guide rather than a technical lecture

#### Scenario: Relationship comfort caution is presented before synastry exists

- **WHEN** the methodology content references relationship ease
- **THEN** it explains that moon harmony matters more than surface agreement for daily comfort
- **AND** it does not present itself as a full synastry verdict

### Requirement: The system SHALL provide ascendant-specific teaching cards for supported rising signs

The product SHALL surface structured topical guidance for supported rising signs, starting with Leo rising and Aquarius rising.

#### Scenario: User expands the themed methodology notes

- **WHEN** the user opens the rising-sign teaching section
- **THEN** the user can review separate cards for Leo rising and Aquarius rising
- **AND** each card includes at least social-mask framing, growth task, emotional caution, and action/resource themes

#### Scenario: Planet lenses are grouped instead of shown as raw notes

- **WHEN** a rising-sign card is rendered
- **THEN** the guidance is grouped into planet-based lenses such as sun, moon, saturn, venus, mars, and mercury/jupiter
- **AND** the group titles make the material scannable for both users and astrologers

### Requirement: The system SHALL contextualize supported rising signs inside the report experience

The report experience SHALL show an ascendant-specific spotlight when the current natal chart matches a supported rising-sign guide.

#### Scenario: A supported rising sign is detected

- **WHEN** the current natal chart ascendant is Leo or Aquarius
- **THEN** the report shows a contextual spotlight card using the corresponding structured guide
- **AND** the spotlight uses concise user-facing language by default

#### Scenario: A non-supported rising sign is detected

- **WHEN** the current natal chart ascendant does not yet have a teaching guide
- **THEN** no empty spotlight shell is shown
- **AND** the rest of the report renders normally
