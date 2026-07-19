# frozen_string_literal: true

require "digest"
require "set"
require_relative "libdragon_sprite_contract"

module N64Game
  # Pure, bounds-checked validation for the pinned Tiny3D v4 on-disk format.
  #
  # Filesystem, Git, Git LFS, and manifest ownership are intentionally handled
  # by scripts/validate-asset-contract. This module accepts already-materialized
  # bytes and refuses any Quarrune model/animation package that the pinned
  # runtime could interpret differently from the reviewed contract.
  module Tiny3DPackageContract
    SCHEMA = "n64game-tiny3d-package-contract-v1".freeze
    BINDING_SCHEMA = "n64game-quarrune-skeleton-binding-v1".freeze
    TINY3D_COMMIT = "e84172f29f719680ac3213a7f408c2f721ef7b24".freeze
    MAGIC = "T3M\x04".b.freeze
    MAX_FILE_BYTES = 32 * 1024 * 1024
    MAX_CHUNKS = 1024
    MAX_KEYFRAMES = 1_000_000
    QUARRUNE_BONE_COUNT = 20
    SKELETON_DOMAIN = "n64game-tiny3d-skeleton-v1\n".b.freeze
    STREAM_SET_DOMAIN = "n64game-quarrune-animation-stream-set-v1\n".b.freeze
    RUNTIME_HELPER_BUNDLE_DOMAIN = "n64game-quarrune-runtime-helper-v1\n".b.freeze
    RUNTIME_HELPER_PATHS = %w[
      src/quarrune_render_assets.c
      src/quarrune_render_assets.h
    ].freeze
    APPROVED_RUNTIME_HELPER_BUNDLE_SHA256 =
      "b9125d3375842e75dc4d0227abbf2158126e1b9ba684842c9f9326071c7b7853".freeze

    MODEL_PRODUCTION_ID = "echo.quarrune".freeze
    ANIMATION_PRODUCTION_ID = "anm.echo.quarrune".freeze
    MODEL_ROLE = "output.tiny3d.model".freeze
    ANIMATION_HEADER_ROLE = "output.tiny3d.animation_header".freeze
    ANIMATION_STREAM_ROLE = "output.tiny3d.animation_stream".freeze
    SKELETON_BINDING_ROLE = "output.skeleton_binding".freeze
    BODY_TEXTURE_ROLE = "output.texture.body".freeze
    ACCENT_TEXTURE_ROLE = "output.texture.accent".freeze
    BLOB_SHADOW_ROLE = "output.blob_shadow.sprite".freeze
    RUNTIME_BINDING_ROLE = "output.runtime_binding".freeze
    RESERVED_ROLES = [
      MODEL_ROLE, ANIMATION_HEADER_ROLE, ANIMATION_STREAM_ROLE, SKELETON_BINDING_ROLE,
      BODY_TEXTURE_ROLE, ACCENT_TEXTURE_ROLE, BLOB_SHADOW_ROLE, RUNTIME_BINDING_ROLE
    ].freeze

    HERO_MODEL_PATH = "review/echo.quarrune/g5/quarrune_hero.t3dm".freeze
    DISTANCE_MODEL_PATH = "review/echo.quarrune/g5/quarrune_distance.t3dm".freeze
    MODEL_PATHS = [DISTANCE_MODEL_PATH, HERO_MODEL_PATH].freeze
    BODY_TEXTURE_PATH = "review/echo.quarrune/g5/tex_quarrune_body_ci8_64x64.sprite".freeze
    ACCENT_TEXTURE_PATH = "review/echo.quarrune/g5/tex_quarrune_accent_ci4_32x32.sprite".freeze
    BLOB_SHADOW_PATH = "review/echo.quarrune/g5/tex_quarrune_blob_shadow_ia8_32x32.sprite".freeze
    RUNTIME_BINDING_PATH = "review/echo.quarrune/g5/RUNTIME_BINDING.tsv".freeze
    BODY_TEXTURE_ROM_PATH = "rom:/echo/echo.quarrune/tex_quarrune_body_ci8_64x64.sprite".freeze
    ACCENT_TEXTURE_ROM_PATH = "rom:/echo/echo.quarrune/tex_quarrune_accent_ci4_32x32.sprite".freeze
    BLOB_SHADOW_ROM_PATH = "rom:/echo/echo.quarrune/tex_quarrune_blob_shadow_ia8_32x32.sprite".freeze
    BODY_TOP_REFERENCE = 0x51554230
    BODY_BOTTOM_REFERENCE = 0x51554231
    QUARRUNE_TEX_SHADE_COMBINER = 0x0012_1824_8833_FFFF
    QUARRUNE_OTHER_MODE_VALUE = 0x0000_0000_0000_0000
    QUARRUNE_OTHER_MODE_MASK = 0x0000_3000_0000_0000
    QUARRUNE_BLEND_MODE = 0x0000_0000
    QUARRUNE_DRAW_FLAGS = 0x0000_0007
    QUARRUNE_FOG_MODE = 0
    QUARRUNE_COLOR_FLAGS = 0
    QUARRUNE_VERTEX_FX = 0
    QUARRUNE_MATERIAL_COLORS = [0, 0, 0, 0].freeze
    MIN_UV_SPAN = 8 * 32
    BODY_DYNAMIC_BINDINGS = [
      { reference: BODY_TOP_REFERENCE, rect: [0, 0, 64, 32] },
      { reference: BODY_BOTTOM_REFERENCE, rect: [0, 32, 64, 64] }
    ].freeze
    MODEL_SPRITE_PATHS = [ACCENT_TEXTURE_PATH, BLOB_SHADOW_PATH, BODY_TEXTURE_PATH].sort.freeze
    ANIMATION_HEADER_PATH = "review/anm.echo.quarrune/g5/anm_echo_quarrune.t3dm".freeze
    SKELETON_BINDING_PATH = "review/anm.echo.quarrune/g5/SKELETON_BINDING.tsv".freeze
    ANIMATION_NAMES = %w[
      brace_relay entrance hit horizon_break idle_a idle_b knockout reposition ridge_ram
    ].freeze
    ANIMATION_STREAM_PATHS = (0...ANIMATION_NAMES.length).map do |index|
      "review/anm.echo.quarrune/g5/anm_echo_quarrune.#{index}.sdata"
    end.freeze
    ANIMATION_ROM_PATHS = (0...ANIMATION_NAMES.length).map do |index|
      "rom:/anm/anm.echo.quarrune/anm_echo_quarrune.#{index}.sdata"
    end.freeze

    BINDING_KEYS = %w[
      schema tiny3d_commit model_production_id animation_production_id hero_model_path
      hero_model_sha256 distance_model_path distance_model_sha256 animation_header_path
      animation_header_sha256 animation_stream_set_sha256 skeleton_signature_sha256
      bone_count animation_names build_id
    ].freeze
    RUNTIME_BINDING_KEYS = %w[
      schema libdragon_commit tiny3d_commit runtime_helper_paths runtime_helper_bundle_sha256
      production_id body_sprite_path body_sprite_sha256
      body_rom_path body_top_reference body_top_rect_px body_bottom_reference body_bottom_rect_px
      body_reference_size_px body_upload_mode material_profile
      accent_sprite_path accent_sprite_sha256 accent_rom_path blob_shadow_sprite_path
      blob_shadow_sprite_sha256 blob_shadow_rom_path blob_shadow_format blob_shadow_size_px
      footprint_mm footprint_offset_mm base_opacity_q8 build_id
    ].freeze
    RUNTIME_BINDING_SCHEMA = "n64game-quarrune-runtime-binding-v1".freeze

    class ParseError < StandardError; end

    class Reader
      def initialize(bytes, label)
        @bytes = bytes
        @label = label
      end

      def raw(offset, length, field)
        unless offset.is_a?(Integer) && length.is_a?(Integer) && offset >= 0 && length >= 0 &&
               offset <= @bytes.bytesize && length <= @bytes.bytesize - offset
          raise ParseError, "#{@label}: #{field} is out of bounds"
        end
        @bytes.byteslice(offset, length)
      end

      def u8(offset, field)
        raw(offset, 1, field).getbyte(0)
      end

      def s8(offset, field)
        raw(offset, 1, field).unpack1("c")
      end

      def u16(offset, field)
        raw(offset, 2, field).unpack1("n")
      end

      def s16(offset, field)
        raw(offset, 2, field).unpack1("s>")
      end

      def u24(offset, field)
        value = raw(offset, 3, field)
        (value.getbyte(0) << 16) | (value.getbyte(1) << 8) | value.getbyte(2)
      end

      def u32(offset, field)
        raw(offset, 4, field).unpack1("N")
      end

      def u64(offset, field)
        raw(offset, 8, field).unpack1("Q>")
      end

      def f32(offset, field)
        raw(offset, 4, field).unpack1("g")
      end
    end

    class ParsedFile
      attr_reader :bytes, :reader, :label, :chunk_count, :total_vertices, :total_indices,
                  :vertex_index, :index_index, :material_index, :string_offset, :aabb_min,
                  :aabb_max, :chunks

      def initialize(bytes, label)
        raise ParseError, "#{label}: bytes must be a String" unless bytes.is_a?(String)
        raise ParseError, "#{label}: file is empty" if bytes.empty?
        raise ParseError, "#{label}: file exceeds #{MAX_FILE_BYTES} bytes" if bytes.bytesize > MAX_FILE_BYTES

        @bytes = bytes.b
        @label = label
        @reader = Reader.new(@bytes, label)
        parse_header
        parse_string_table
      end

      def types
        @chunks.map { |chunk| chunk[:type] }.join
      end

      def chunks_of(type)
        @chunks.select { |chunk| chunk[:type] == type }
      end

      def string_at(offset, field)
        unless offset.is_a?(Integer) && offset >= 1 && offset < @string_table.bytesize
          raise ParseError, "#{@label}: #{field} string offset is outside the string table"
        end
        terminator = @string_table.index("\0".b, offset)
        raise ParseError, "#{@label}: #{field} string is not NUL terminated" unless terminator

        raw = @string_table.byteslice(offset, terminator - offset)
        raise ParseError, "#{@label}: #{field} string is empty" if raw.empty?
        utf8 = raw.dup.force_encoding(Encoding::UTF_8)
        raise ParseError, "#{@label}: #{field} string is not valid UTF-8" unless utf8.valid_encoding?
        raise ParseError, "#{@label}: #{field} string contains a control character" if utf8.match?(/[\x00-\x1f\x7f]/)
        utf8
      end

      def chunk_bytes(chunk)
        @reader.raw(chunk[:offset], chunk[:size], "#{chunk[:type]} chunk")
      end

      def require_zero_tail(chunk, used, field)
        if used > chunk[:size]
          raise ParseError, "#{@label}: #{field} crosses its chunk boundary"
        end
        tail = @reader.raw(chunk[:offset] + used, chunk[:size] - used, "#{field} padding")
        raise ParseError, "#{@label}: #{field} has nonzero padding or trailing payload" unless zero_bytes?(tail)
      end

      private

      def parse_header
        raise ParseError, "#{@label}: file is shorter than the Tiny3D header" if @bytes.bytesize < 0x2C
        raise ParseError, "#{@label}: magic/version is not pinned Tiny3D v4" unless @reader.raw(0, 4, "magic") == MAGIC

        @chunk_count = @reader.u32(0x04, "chunk count")
        unless @chunk_count.positive? && @chunk_count <= MAX_CHUNKS
          raise ParseError, "#{@label}: chunk count is outside the contract"
        end
        table_end = 0x2C + (@chunk_count * 4)
        raise ParseError, "#{@label}: chunk table is truncated" if table_end > @bytes.bytesize

        @total_vertices = @reader.u16(0x08, "total vertex count")
        @total_indices = @reader.u16(0x0A, "total index count")
        @vertex_index = @reader.u32(0x0C, "vertex chunk index")
        @index_index = @reader.u32(0x10, "index chunk index")
        @material_index = @reader.u32(0x14, "material chunk index")
        @string_offset = @reader.u32(0x18, "string table offset")
        raise ParseError, "#{@label}: on-disk runtime block is nonzero" unless @reader.u32(0x1C, "runtime block").zero?
        unless @string_offset >= table_end && @string_offset <= @bytes.bytesize && (@string_offset % 4).zero?
          raise ParseError, "#{@label}: string table offset is invalid or unaligned"
        end

        @aabb_min = 3.times.map { |axis| @reader.s16(0x20 + axis * 2, "AABB minimum") }
        @aabb_max = 3.times.map { |axis| @reader.s16(0x26 + axis * 2, "AABB maximum") }
        raw_chunks = @chunk_count.times.map do |index|
          entry = 0x2C + index * 4
          type_byte = @reader.u8(entry, "chunk #{index} type")
          unless type_byte >= 0x21 && type_byte <= 0x7E
            raise ParseError, "#{@label}: chunk #{index} type is not printable ASCII"
          end
          {
            index: index,
            type: type_byte.chr,
            offset: @reader.u24(entry + 1, "chunk #{index} offset")
          }
        end
        offsets = raw_chunks.map { |chunk| chunk[:offset] }
        unless offsets.all? { |offset| offset >= table_end && offset <= @string_offset }
          raise ParseError, "#{@label}: a chunk offset overlaps the header or string table"
        end
        unless offsets.each_cons(2).all? { |left, right| left <= right }
          raise ParseError, "#{@label}: chunk offsets decrease"
        end

        @chunks = raw_chunks.each_with_index.map do |chunk, index|
          following = raw_chunks[(index + 1)..-1].to_a.find { |candidate| candidate[:offset] > chunk[:offset] }
          run_continues = index + 1 < raw_chunks.length && raw_chunks[index + 1][:offset] == chunk[:offset]
          boundary = following ? following[:offset] : @string_offset
          chunk.merge(size: run_continues ? 0 : boundary - chunk[:offset])
        end
        first_offset = @chunks.first[:offset]
        header_padding = @reader.raw(table_end, first_offset - table_end, "header padding")
        raise ParseError, "#{@label}: header padding is nonzero" unless zero_bytes?(header_padding)
      end

      def parse_string_table
        @string_table = @reader.raw(@string_offset, @bytes.bytesize - @string_offset, "string table")
        raise ParseError, "#{@label}: string table lacks the S sentinel" if @string_table.empty? || @string_table.getbyte(0) != 0x53
        cursor = 1
        while cursor < @string_table.bytesize
          terminator = @string_table.index("\0".b, cursor)
          raise ParseError, "#{@label}: stored string is not NUL terminated" unless terminator
          raw = @string_table.byteslice(cursor, terminator - cursor)
          raise ParseError, "#{@label}: stored string is empty" if raw.empty?
          utf8 = raw.dup.force_encoding(Encoding::UTF_8)
          raise ParseError, "#{@label}: stored string is not valid UTF-8" unless utf8.valid_encoding?
          raise ParseError, "#{@label}: stored string contains a control character" if utf8.match?(/[\x00-\x1f\x7f]/)
          cursor = terminator + 1
        end
      end

      def zero_bytes?(bytes)
        bytes.each_byte.all?(&:zero?)
      end
    end

    module_function

    def validate_pair(model_entries:, animation_entries:, bytes_by_path:, model_build_id:, animation_build_id:)
      issues = []
      unless model_entries.is_a?(Array) && animation_entries.is_a?(Array) && bytes_by_path.is_a?(Hash)
        return ["Quarrune Tiny3D pair inputs have invalid container types"]
      end

      model_entries = normalize_entries(model_entries, "model", issues)
      animation_entries = normalize_entries(animation_entries, "animation", issues)
      validate_entry_census(model_entries, animation_entries, model_build_id, animation_build_id, issues)
      return issues unless issues.empty?

      all_entries = model_entries + animation_entries
      all_entries.each do |entry|
        bytes = bytes_by_path[entry[:path]] || bytes_by_path[entry[:path].to_sym]
        unless bytes.is_a?(String)
          issues << "#{entry[:path]} has no materialized bytes"
          next
        end
        issues << "#{entry[:path]} byte count differs from its manifest entry" unless bytes.bytesize == entry[:count]
        issues << "#{entry[:path]} SHA-256 differs from its manifest entry" unless Digest::SHA256.hexdigest(bytes) == entry[:digest]
      end
      return issues unless issues.empty?

      decoded_models = {}
      MODEL_PATHS.each do |path|
        begin
          decoded_models[path] = decode_model(bytes_by_path[path] || bytes_by_path[path.to_sym], path)
        rescue ParseError => error
          issues << error.message
        end
      end

      decoded_animation = nil
      begin
        stream_bytes = ANIMATION_STREAM_PATHS.each_with_object({}) do |path, values|
          values[path] = bytes_by_path[path] || bytes_by_path[path.to_sym]
        end
        decoded_animation = decode_animation(
          bytes_by_path[ANIMATION_HEADER_PATH] || bytes_by_path[ANIMATION_HEADER_PATH.to_sym],
          stream_bytes,
          ANIMATION_HEADER_PATH
        )
      rescue ParseError => error
        issues << error.message
      end
      return issues unless issues.empty?

      begin
        validate_production_model_pair(decoded_models)
        decoded_sprites = {
          BODY_TEXTURE_PATH => N64Game::LibdragonSpriteContract.validate_profile(
            bytes_by_path[BODY_TEXTURE_PATH] || bytes_by_path[BODY_TEXTURE_PATH.to_sym],
            label: BODY_TEXTURE_PATH, format: "CI8", width: 64, height: 64, fits_tmem: false
          ),
          ACCENT_TEXTURE_PATH => N64Game::LibdragonSpriteContract.validate_profile(
            bytes_by_path[ACCENT_TEXTURE_PATH] || bytes_by_path[ACCENT_TEXTURE_PATH.to_sym],
            label: ACCENT_TEXTURE_PATH, format: "CI4", width: 32, height: 32, fits_tmem: true
          ),
          BLOB_SHADOW_PATH => N64Game::LibdragonSpriteContract.validate_profile(
            bytes_by_path[BLOB_SHADOW_PATH] || bytes_by_path[BLOB_SHADOW_PATH.to_sym],
            label: BLOB_SHADOW_PATH, format: "IA8", width: 32, height: 32, fits_tmem: true
          )
        }
        validate_sprite_content(decoded_sprites)
        runtime_binding = parse_runtime_binding(
          bytes_by_path[RUNTIME_BINDING_PATH] || bytes_by_path[RUNTIME_BINDING_PATH.to_sym],
          RUNTIME_BINDING_PATH
        )
        expected_runtime = expected_runtime_binding(model_entries, model_build_id)
        RUNTIME_BINDING_KEYS.each do |key|
          issues << "#{RUNTIME_BINDING_PATH}: #{key} binding mismatch" unless
            runtime_binding[key] == expected_runtime[key]
        end
      rescue ParseError => error
        issues << error.message
      end
      return issues unless issues.empty?

      signatures = MODEL_PATHS.map { |path| decoded_models[path][:skeleton_signature] }
      signatures << decoded_animation[:skeleton_signature]
      issues << "Quarrune hero, distance, and animation skeleton signatures differ" unless signatures.uniq.length == 1

      binding_bytes = bytes_by_path[SKELETON_BINDING_PATH] || bytes_by_path[SKELETON_BINDING_PATH.to_sym]
      begin
        binding = parse_binding(binding_bytes, SKELETON_BINDING_PATH)
        expected = expected_binding(
          model_entries, animation_entries, signatures.first, model_build_id
        )
        BINDING_KEYS.each do |key|
          issues << "#{SKELETON_BINDING_PATH}: #{key} binding mismatch" unless binding[key] == expected[key]
        end
      rescue ParseError => error
        issues << error.message
      end
      issues
    rescue StandardError => error
      ["Quarrune Tiny3D pair validator failed closed: #{error.class}: #{error.message}"]
    end

    def runtime_helper_bundle_sha256(members)
      return nil unless members.is_a?(Hash) && members.keys.map(&:to_s).sort == RUNTIME_HELPER_PATHS.sort

      digest = Digest::SHA256.new
      digest.update(RUNTIME_HELPER_BUNDLE_DOMAIN)
      RUNTIME_HELPER_PATHS.sort.each do |path|
        bytes = members[path] || members[path.to_sym]
        return nil unless bytes.is_a?(String)

        digest.update("#{path}\t#{Digest::SHA256.hexdigest(bytes)}\n")
      end
      digest.hexdigest
    end

    def validate_production_model_pair(decoded_models)
      hero = decoded_models.fetch(HERO_MODEL_PATH)
      distance = decoded_models.fetch(DISTANCE_MODEL_PATH)
      unless hero[:triangle_count].between?(850, 1250)
        raise ParseError, "#{HERO_MODEL_PATH}: triangle count must remain within the reviewed 850-1250 hero budget"
      end
      unless distance[:triangle_count].positive? && distance[:triangle_count] <= 650 &&
             distance[:triangle_count] * 100 >= hero[:triangle_count] * 45 &&
             distance[:triangle_count] * 100 <= hero[:triangle_count] * 60
        raise ParseError, "#{DISTANCE_MODEL_PATH}: triangle count must be at most 650 and 45-60 percent of hero"
      end
      decoded_models.each do |path, model|
        unless model[:material_count] == 3 && model[:used_material_indices] == [0, 1, 2]
          raise ParseError, "#{path}: Quarrune must contain exactly three materials and use every one"
        end
        names = model[:materials].map { |material| material[:name] }
        raise ParseError, "#{path}: Quarrune material names must be unique" unless names.uniq.length == 3
        active = model[:materials].map do |material|
          texture_a, texture_b = material[:textures]
          unless active_texture?(texture_a) && empty_texture?(texture_b)
            raise ParseError, "#{path}: every Quarrune material must bind exactly one texture in slot A/TILE0 and leave slot B empty"
          end
          unless material[:color_combiner] == QUARRUNE_TEX_SHADE_COMBINER &&
                 material[:other_mode_value] == QUARRUNE_OTHER_MODE_VALUE &&
                 material[:other_mode_mask] == QUARRUNE_OTHER_MODE_MASK &&
                 material[:blend_mode] == QUARRUNE_BLEND_MODE &&
                 material[:draw_flags] == QUARRUNE_DRAW_FLAGS &&
                 material[:fog] == QUARRUNE_FOG_MODE &&
                 material[:color_flags] == QUARRUNE_COLOR_FLAGS &&
                 material[:vertex_fx] == QUARRUNE_VERTEX_FX &&
                 material[:prim_color] == QUARRUNE_MATERIAL_COLORS &&
                 material[:env_color] == QUARRUNE_MATERIAL_COLORS &&
                 material[:blend_color] == QUARRUNE_MATERIAL_COLORS
            raise ParseError, "#{path}: Quarrune material render state must exactly use TEX0 x SHADE, opaque blending, depth/textured/shaded flags, point filtering, default fog/colors, and ordinary UVs"
          end
          texture_a
        end
        dynamic = active.select { |texture| texture[:reference].positive? }
        static = active.select { |texture| texture[:path] }
        unless dynamic.map { |texture| texture[:reference] }.sort ==
               [BODY_TOP_REFERENCE, BODY_BOTTOM_REFERENCE].sort
          raise ParseError, "#{path}: body materials must use the exact two pathless CI8 region references"
        end
        dynamic.each do |texture|
          unless texture[:path].nil? && texture[:width] == 64 && texture[:height] == 32 &&
                 canonical_axes?(texture[:axes], 64, 32)
            raise ParseError, "#{path}: dynamic body region dimensions/tile parameters are not canonical"
          end
        end
        unless static.length == 1 && static.first[:reference].zero? &&
               static.first[:path] == ACCENT_TEXTURE_ROM_PATH &&
               static.first[:width] == 32 && static.first[:height] == 32 &&
               canonical_axes?(static.first[:axes], 32, 32)
          raise ParseError, "#{path}: accent material must use the exact static 32x32 CI4 sprite"
        end

        model[:objects].each_with_index do |object, object_index|
          texture = model[:materials].fetch(object[:material])[:textures].first
          maximum_s = texture[:width] * 32
          maximum_t = texture[:height] * 32
          unless object[:drawn_source_uvs].all? do |s, t|
                   s.between?(0, maximum_s) && t.between?(0, maximum_t)
                 end
            raise ParseError, "#{path}: object #{object_index} packed UVs leave its region-local texture bounds"
          end
        end
        3.times do |material_index|
          uvs = model[:objects].select { |object| object[:material] == material_index }
                               .flat_map { |object| object[:drawn_source_uvs] }
          s_values = uvs.map(&:first)
          t_values = uvs.map(&:last)
          unless s_values.max - s_values.min >= MIN_UV_SPAN &&
                 t_values.max - t_values.min >= MIN_UV_SPAN
            raise ParseError, "#{path}: material #{material_index} UV island is too collapsed to be an authored texture mapping"
          end
        end
      end
    end

    def active_texture?(texture)
      texture[:reference].positive? || !texture[:path].nil?
    end

    def empty_texture?(texture)
      texture[:reference].zero? && texture[:path].nil? && texture[:hash].zero? &&
        texture[:width].zero? && texture[:height].zero? &&
        texture[:axes].all? do |axis|
          axis[:low] == 0.0 && axis[:high] == 0.0 && axis[:mask].zero? &&
            axis[:shift].zero? && axis[:mirror].zero? && axis[:clamp].zero?
        end
    end

    def canonical_axes?(axes, width, height)
      expected_high = [width - 1, height - 1]
      axes.each_with_index.all? do |axis, index|
        axis[:low] == 0.0 && axis[:high] == expected_high[index].to_f &&
          axis[:mask].zero? && axis[:shift].zero? && axis[:mirror].zero? && axis[:clamp] == 1
      end
    end

    def validate_sprite_content(decoded_sprites)
      {
        BODY_TEXTURE_PATH => 32,
        ACCENT_TEXTURE_PATH => 8
      }.each do |path, minimum_colors|
        sprite = decoded_sprites.fetch(path)
        used = sprite[:indices].to_set
        unless sprite[:palette_used] >= minimum_colors && used == (0...sprite[:palette_used]).to_set
          raise ParseError, "#{path}: texture must use a contiguous intentional palette of at least #{minimum_colors} colors"
        end
        used_palette = sprite[:palette].first(sprite[:palette_used])
        unless used_palette.uniq.length == used_palette.length && used_palette.all? { |color| (color & 1) == 1 }
          raise ParseError, "#{path}: used material palette colors must be unique and opaque"
        end
        luminance = used_palette.map do |color|
          red = (color >> 11) & 0x1F
          green = (color >> 6) & 0x1F
          blue = (color >> 1) & 0x1F
          red * 3 + green * 6 + blue
        end
        unless luminance.max - luminance.min >= 24
          raise ParseError, "#{path}: used material palette lacks a readable value range"
        end
      end

      shadow = decoded_sprites.fetch(BLOB_SHADOW_PATH)
      pixels = shadow[:pixel_data].bytes
      alpha = pixels.map { |byte| byte & 0x0F }
      border = []
      32.times do |index|
        border.concat([alpha[index], alpha[31 * 32 + index], alpha[index * 32], alpha[index * 32 + 31]])
      end
      raise ParseError, "#{BLOB_SHADOW_PATH}: blob shadow perimeter must be transparent" unless border.all?(&:zero?)
      covered = alpha.each_index.select { |index| alpha[index].positive? }
      unless covered.length.between?(128, 800) && alpha.uniq.length >= 5 && alpha.max >= 10
        raise ParseError, "#{BLOB_SHADOW_PATH}: blob shadow coverage/alpha ramp is not authored"
      end
      center_alpha = [alpha[15 * 32 + 15], alpha[15 * 32 + 16], alpha[16 * 32 + 15], alpha[16 * 32 + 16]].max
      raise ParseError, "#{BLOB_SHADOW_PATH}: blob shadow center is not opaque enough" unless center_alpha >= 10
      total_weight = alpha.sum
      centroid_x = alpha.each_with_index.sum { |value, index| value * (index % 32) }.to_f / total_weight
      centroid_y = alpha.each_with_index.sum { |value, index| value * (index / 32) }.to_f / total_weight
      unless centroid_x.between?(12.0, 19.0) && centroid_y.between?(12.0, 19.0)
        raise ParseError, "#{BLOB_SHADOW_PATH}: blob shadow weighted center leaves the authored footprint"
      end
      unless connected_mask?(covered.to_set, 32, 32)
        raise ParseError, "#{BLOB_SHADOW_PATH}: blob shadow alpha mask contains disconnected islands"
      end
    end

    def connected_mask?(mask, width, height)
      return false if mask.empty?

      remaining = mask.dup
      stack = [remaining.first]
      remaining.delete(stack.first)
      until stack.empty?
        index = stack.pop
        x = index % width
        y = index / width
        (-1..1).each do |dy|
          (-1..1).each do |dx|
            next if dx.zero? && dy.zero?
            nx = x + dx
            ny = y + dy
            next unless nx.between?(0, width - 1) && ny.between?(0, height - 1)
            neighbor = ny * width + nx
            next unless remaining.delete?(neighbor)
            stack << neighbor
          end
        end
      end
      remaining.empty?
    end

    def decode_model(bytes, label = "Tiny3D model")
      file = ParsedFile.new(bytes, label)
      types = file.types
      unless types.match?(/\AO+B?VIM+S\z/)
        raise ParseError, "#{label}: model chunk sequence must be O+,[B],V,I,M+,S; got #{types.inspect}"
      end
      objects = file.chunks_of("O")
      bvh_chunk = file.chunks_of("B").first
      materials = file.chunks_of("M")
      vertex_chunk = file.chunks_of("V").first
      index_chunk = file.chunks_of("I").first
      skeleton_chunk = file.chunks_of("S").first
      validate_chunk_alignments(file, "O" => 8, "B" => 8, "V" => 16, "I" => 4, "M" => 8, "S" => 8)
      expected_vertex_index = objects.length + (bvh_chunk ? 1 : 0)
      expected_index_index = expected_vertex_index + 1
      expected_material_index = expected_index_index + 1
      unless file.vertex_index == expected_vertex_index && file.index_index == expected_index_index &&
             file.material_index == expected_material_index
        raise ParseError, "#{label}: header chunk indices do not match the model sequence"
      end
      unless file.total_vertices.positive? && file.total_vertices.even?
        raise ParseError, "#{label}: model vertex count must be positive and even"
      end
      unless 3.times.all? { |axis| file.aabb_min[axis] <= file.aabb_max[axis] }
        raise ParseError, "#{label}: model AABB is inverted"
      end

      vertex_bytes = file.total_vertices * 16
      unless vertex_chunk[:size] == vertex_bytes
        raise ParseError, "#{label}: V chunk size does not equal totalVertCount * 16"
      end
      skeleton = parse_skeleton(file, skeleton_chunk, QUARRUNE_BONE_COUNT)
      object_data = objects.map.with_index do |chunk, index|
        parse_object(
          file, chunk, index, materials.length, vertex_chunk, vertex_bytes,
          QUARRUNE_BONE_COUNT
        )
      end
      covered_vertices = object_data.flat_map { |object| object[:source_vertices] }.sort
      unless covered_vertices == (0...file.total_vertices).to_a
        raise ParseError, "#{label}: object-part source ranges do not cover the exact V chunk"
      end
      object_minimum = 3.times.map { |axis| object_data.map { |object| object[:minimum][axis] }.min }
      object_maximum = 3.times.map { |axis| object_data.map { |object| object[:maximum][axis] }.max }
      unless file.aabb_min == object_minimum && file.aabb_max == object_maximum
        raise ParseError, "#{label}: model AABB is not the exact union of object AABBs"
      end
      parse_bvh(file, bvh_chunk, object_data) if bvh_chunk
      material_data = parse_materials(file, materials)
      validate_index_layout(file, index_chunk, object_data)

      {
        schema: SCHEMA,
        kind: "model",
        object_count: objects.length,
        has_bvh: !bvh_chunk.nil?,
        material_count: materials.length,
        materials: material_data,
        objects: object_data,
        used_material_indices: object_data.map { |object| object[:material] }.uniq.sort,
        triangle_count: object_data.sum { |object| object[:triangle_count] },
        vertex_count: file.total_vertices,
        index_count: file.total_indices,
        bone_count: skeleton[:bones].length,
        skeleton_signature: skeleton[:signature],
        bone_names: skeleton[:bones].map { |bone| bone[:name] }
      }
    end

    def decode_animation(bytes, streams, label = "Tiny3D animation package")
      raise ParseError, "#{label}: streams must be a Hash" unless streams.is_a?(Hash)
      file = ParsedFile.new(bytes, label)
      expected_types = ("A" * ANIMATION_NAMES.length) + "VIS"
      unless file.types == expected_types
        raise ParseError, "#{label}: animation chunk sequence must be #{expected_types}; got #{file.types.inspect}"
      end
      validate_chunk_alignments(file, "A" => 4, "V" => 16, "I" => 4, "S" => 8)
      unless file.total_vertices.zero? && file.total_indices.zero?
        raise ParseError, "#{label}: animation-only header contains geometry counts"
      end
      unless file.vertex_index == ANIMATION_NAMES.length &&
             file.index_index == ANIMATION_NAMES.length + 1 &&
             file.material_index == ANIMATION_NAMES.length + 2
        raise ParseError, "#{label}: animation header chunk indices differ from pinned writer output"
      end
      unless file.aabb_min == [32_767, 32_767, 32_767] && file.aabb_max == [-32_768, -32_768, -32_768]
        raise ParseError, "#{label}: animation-only AABB sentinels differ from pinned writer output"
      end
      vertex_chunk = file.chunks_of("V").first
      index_chunk = file.chunks_of("I").first
      unless vertex_chunk[:size].zero? && index_chunk[:size].zero?
        raise ParseError, "#{label}: animation-only V/I chunks must be zero length"
      end

      skeleton = parse_skeleton(file, file.chunks_of("S").first, QUARRUNE_BONE_COUNT)
      animations = file.chunks_of("A").map.with_index do |chunk, index|
        parse_animation_chunk(file, chunk, index, QUARRUNE_BONE_COUNT)
      end
      names = animations.map { |animation| animation[:name] }
      raise ParseError, "#{label}: animation names/order differ from the exact nine-clip contract" unless names == ANIMATION_NAMES

      expected_stream_keys = ANIMATION_STREAM_PATHS
      actual_stream_keys = streams.keys.map(&:to_s).sort
      unless actual_stream_keys == expected_stream_keys.sort
        raise ParseError, "#{label}: stream file set differs from exact .0.sdata-.8.sdata contract"
      end
      animations.each_with_index do |animation, index|
        path = ANIMATION_STREAM_PATHS[index]
        stream = streams[path] || streams[path.to_sym]
        parse_stream(stream, animation, path)
      end

      {
        schema: SCHEMA,
        kind: "animation",
        animation_names: names,
        animation_count: animations.length,
        stream_count: expected_stream_keys.length,
        bone_count: skeleton[:bones].length,
        skeleton_signature: skeleton[:signature],
        bone_names: skeleton[:bones].map { |bone| bone[:name] }
      }
    end

    def normalize_entries(entries, label, issues)
      entries.each_with_index.map do |entry, index|
        unless entry.is_a?(Hash)
          issues << "Quarrune #{label} manifest entry #{index + 1} is not a Hash"
          next({})
        end
        normalized = {}
        %i[path role digest count build capture kind mode].each do |key|
          normalized[key] = entry[key] || entry[key.to_s]
        end
        normalized[:path] = normalized[:path].to_s
        normalized[:role] = normalized[:role].to_s
        normalized[:digest] = normalized[:digest].to_s
        normalized[:build] = normalized[:build].to_s
        normalized[:capture] = normalized[:capture].to_s
        normalized[:kind] = normalized[:kind].to_s
        normalized[:mode] = normalized[:mode].to_s
        normalized[:count] = Integer(normalized[:count]) rescue -1
        normalized
      end
    end

    def validate_entry_census(model_entries, animation_entries, model_build_id, animation_build_id, issues)
      unless model_build_id.is_a?(String) && !model_build_id.empty? && model_build_id != "-" &&
             animation_build_id == model_build_id
        issues << "Quarrune model and animation packages require one shared substantive build ID"
      end

      model_t3d = model_entries.select { |entry| File.extname(entry[:path].to_s).downcase == ".t3dm" }
      model_streams = model_entries.select { |entry| File.extname(entry[:path].to_s).downcase == ".sdata" }
      model_sprites = model_entries.select { |entry| File.extname(entry[:path].to_s).downcase == ".sprite" }
      model_role_entries = model_entries.select { |entry| entry[:role] == MODEL_ROLE }
      issues << "echo.quarrune output must contain exactly the hero and distance T3DM files" unless
        model_t3d.map { |entry| entry[:path] }.sort == MODEL_PATHS
      issues << "output.tiny3d.model role may name only the canonical hero and distance files" unless
        model_role_entries.map { |entry| entry[:path] }.sort == MODEL_PATHS
      issues << "echo.quarrune output must not own animation streams" unless model_streams.empty?
      issues << "echo.quarrune output must contain exactly the body, accent, and blob-shadow sprites" unless
        model_sprites.map { |entry| entry[:path] }.sort == MODEL_SPRITE_PATHS
      model_t3d.each do |entry|
        issues << "#{entry[:path]} has the wrong model role" unless entry[:role] == MODEL_ROLE
      end
      issues << "echo.quarrune output must not own the skeleton binding" if
        model_entries.any? { |entry| entry[:role] == SKELETON_BINDING_ROLE || entry[:path] == SKELETON_BINDING_PATH }
      expected_model_reserved = MODEL_PATHS.map { |path| [MODEL_ROLE, path] } + [
        [BODY_TEXTURE_ROLE, BODY_TEXTURE_PATH],
        [ACCENT_TEXTURE_ROLE, ACCENT_TEXTURE_PATH],
        [BLOB_SHADOW_ROLE, BLOB_SHADOW_PATH],
        [RUNTIME_BINDING_ROLE, RUNTIME_BINDING_PATH]
      ]
      actual_model_reserved = model_entries.select { |entry| RESERVED_ROLES.include?(entry[:role]) }
                                           .map { |entry| [entry[:role], entry[:path]] }.sort
      issues << "echo.quarrune reserved package roles differ from the exact model/texture/shadow/binding mapping" unless
        actual_model_reserved == expected_model_reserved.sort
      {
        BODY_TEXTURE_PATH => BODY_TEXTURE_ROLE,
        ACCENT_TEXTURE_PATH => ACCENT_TEXTURE_ROLE,
        BLOB_SHADOW_PATH => BLOB_SHADOW_ROLE
      }.each do |path, role|
        entry = model_sprites.find { |candidate| candidate[:path] == path }
        issues << "#{path} has the wrong sprite role" unless entry && entry[:role] == role
      end
      runtime_bindings = model_entries.select do |entry|
        entry[:path] == RUNTIME_BINDING_PATH || entry[:role] == RUNTIME_BINDING_ROLE
      end
      issues << "echo.quarrune output must contain exactly one canonical runtime binding" unless
        runtime_bindings.map { |entry| entry[:path] } == [RUNTIME_BINDING_PATH]
      runtime_bindings.each do |entry|
        issues << "#{entry[:path]} has the wrong runtime-binding role" unless entry[:role] == RUNTIME_BINDING_ROLE
      end

      animation_t3d = animation_entries.select { |entry| File.extname(entry[:path].to_s).downcase == ".t3dm" }
      animation_streams = animation_entries.select { |entry| File.extname(entry[:path].to_s).downcase == ".sdata" }
      animation_header_roles = animation_entries.select { |entry| entry[:role] == ANIMATION_HEADER_ROLE }
      animation_stream_roles = animation_entries.select { |entry| entry[:role] == ANIMATION_STREAM_ROLE }
      bindings = animation_entries.select do |entry|
        entry[:role] == SKELETON_BINDING_ROLE || entry[:path] == SKELETON_BINDING_PATH
      end
      issues << "anm.echo.quarrune output must contain exactly one canonical animation T3DM header" unless
        animation_t3d.map { |entry| entry[:path] } == [ANIMATION_HEADER_PATH]
      issues << "anm.echo.quarrune output must contain the exact nine canonical streams" unless
        animation_streams.map { |entry| entry[:path] }.sort == ANIMATION_STREAM_PATHS.sort
      issues << "output.tiny3d.animation_header role may name only the canonical header" unless
        animation_header_roles.map { |entry| entry[:path] } == [ANIMATION_HEADER_PATH]
      issues << "output.tiny3d.animation_stream role may name only the exact nine streams" unless
        animation_stream_roles.map { |entry| entry[:path] }.sort == ANIMATION_STREAM_PATHS.sort
      issues << "anm.echo.quarrune output must contain exactly one canonical skeleton binding" unless
        bindings.map { |entry| entry[:path] } == [SKELETON_BINDING_PATH]
      animation_t3d.each do |entry|
        issues << "#{entry[:path]} has the wrong animation-header role" unless entry[:role] == ANIMATION_HEADER_ROLE
      end
      animation_streams.each do |entry|
        issues << "#{entry[:path]} has the wrong animation-stream role" unless entry[:role] == ANIMATION_STREAM_ROLE
      end
      bindings.each do |entry|
        issues << "#{entry[:path]} has the wrong skeleton-binding role" unless entry[:role] == SKELETON_BINDING_ROLE
      end
      expected_animation_reserved = [[ANIMATION_HEADER_ROLE, ANIMATION_HEADER_PATH]] +
                                    ANIMATION_STREAM_PATHS.map { |path| [ANIMATION_STREAM_ROLE, path] } +
                                    [[SKELETON_BINDING_ROLE, SKELETON_BINDING_PATH]]
      actual_animation_reserved = animation_entries.select { |entry| RESERVED_ROLES.include?(entry[:role]) }
                                                   .map { |entry| [entry[:role], entry[:path]] }
      issues << "anm.echo.quarrune reserved Tiny3D roles differ from the exact header/stream/binding mapping" unless
        actual_animation_reserved.sort == expected_animation_reserved.sort

      relevant = model_t3d + model_sprites + runtime_bindings + animation_t3d + animation_streams + bindings
      relevant.each do |entry|
        issues << "#{entry[:path]} manifest build differs from the pair build" unless entry[:build] == model_build_id
        issues << "#{entry[:path]} must use capture:-" unless entry[:capture] == "-"
        issues << "#{entry[:path]} digest is malformed" unless entry[:digest].match?(/\A[0-9a-f]{64}\z/)
        issues << "#{entry[:path]} byte count is invalid" unless entry[:count] >= 0
        issues << "#{entry[:path]} must use mode 100644" unless entry[:mode] == "100644"
        expected_kind = [SKELETON_BINDING_PATH, RUNTIME_BINDING_PATH].include?(entry[:path]) ? "git" : "lfs"
        issues << "#{entry[:path]} storage kind must be #{expected_kind}" unless entry[:kind] == expected_kind
      end
      if model_t3d.length == 2 && model_t3d.map { |entry| entry[:digest] }.uniq.length != 2
        issues << "Quarrune hero and distance models must be distinct converted artifacts"
      end
      if animation_streams.length == ANIMATION_STREAM_PATHS.length &&
         animation_streams.map { |entry| entry[:digest] }.uniq.length != ANIMATION_STREAM_PATHS.length
        issues << "Quarrune nine animation streams must be distinct performances"
      end
    end

    def parse_skeleton(file, chunk, expected_count)
      raise ParseError, "#{file.label}: skeleton chunk is missing" unless chunk
      base = chunk[:offset]
      count = file.reader.u16(base, "skeleton bone count")
      reserved = file.reader.u16(base + 2, "skeleton reserved field")
      raise ParseError, "#{file.label}: skeleton reserved field is nonzero" unless reserved.zero?
      raise ParseError, "#{file.label}: skeleton must contain exactly #{expected_count} bones" unless count == expected_count
      logical_size = 4 + count * 48
      file.require_zero_tail(chunk, logical_size, "skeleton chunk")

      bones = count.times.map do |index|
        offset = base + 4 + index * 48
        name = file.string_at(file.reader.u32(offset, "bone #{index} name"), "bone #{index} name")
        unless name.match?(/\A[A-Za-z][A-Za-z0-9_.-]{0,63}\z/)
          raise ParseError, "#{file.label}: bone #{index} name is noncanonical"
        end
        parent = file.reader.u16(offset + 4, "bone #{index} parent")
        depth = file.reader.u16(offset + 6, "bone #{index} depth")
        transform_raw = file.reader.raw(offset + 8, 40, "bone #{index} rest transform")
        values = 10.times.map { |value| file.reader.f32(offset + 8 + value * 4, "bone #{index} rest transform") }
        raise ParseError, "#{file.label}: bone #{index} rest transform is non-finite" unless values.all?(&:finite?)
        scales = values[0, 3]
        raise ParseError, "#{file.label}: bone #{index} scale must be positive" unless scales.all? { |scale| scale.positive? }
        quat = values[3, 4]
        norm = Math.sqrt(quat.sum { |component| component * component })
        unless (norm - 1.0).abs <= 0.01
          raise ParseError, "#{file.label}: bone #{index} rest quaternion is not normalized"
        end
        { index: index, name: name, parent: parent, depth: depth, transform_raw: transform_raw }
      end
      raise ParseError, "#{file.label}: skeleton bone names are not unique" unless bones.map { |bone| bone[:name] }.uniq.length == count
      bones.each_with_index do |bone, index|
        if index.zero?
          unless bone[:parent] == 0xFFFF && bone[:depth].zero?
            raise ParseError, "#{file.label}: bone zero must be the sole depth-zero root"
          end
        else
          unless bone[:parent] < index && bone[:parent] != 0xFFFF
            raise ParseError, "#{file.label}: bone #{index} parent must precede the child"
          end
          expected_depth = bones[bone[:parent]][:depth] + 1
          unless bone[:depth] == expected_depth
            raise ParseError, "#{file.label}: bone #{index} depth does not match its parent"
          end
        end
      end
      signature_payload = SKELETON_DOMAIN.dup
      signature_payload << [count].pack("n")
      bones.each do |bone|
        name = bone[:name].encode(Encoding::UTF_8).b
        signature_payload << [bone[:index], name.bytesize].pack("n2")
        signature_payload << name
        signature_payload << [bone[:parent], bone[:depth]].pack("n2")
        signature_payload << bone[:transform_raw]
      end
      { bones: bones, signature: Digest::SHA256.hexdigest(signature_payload) }
    end

    def parse_object(file, chunk, object_index, material_count, vertex_chunk, vertex_bytes, bone_count)
      base = chunk[:offset]
      name = file.string_at(file.reader.u32(base, "object #{object_index} name"), "object #{object_index} name")
      part_count = file.reader.u16(base + 4, "object #{object_index} part count")
      triangle_count = file.reader.u16(base + 6, "object #{object_index} triangle count")
      material = file.reader.u32(base + 8, "object #{object_index} material")
      raise ParseError, "#{file.label}: object #{object_index} has no parts or triangles" unless part_count.positive? && triangle_count.positive?
      raise ParseError, "#{file.label}: object #{object_index} material ordinal is out of range" unless material < material_count
      raise ParseError, "#{file.label}: object #{object_index} runtime block is nonzero" unless file.reader.u32(base + 12, "object runtime block").zero?
      runtime = file.reader.raw(base + 16, 4, "object runtime bytes")
      raise ParseError, "#{file.label}: object #{object_index} runtime/padding bytes are nonzero" unless runtime.each_byte.all?(&:zero?)
      minimum = 3.times.map { |axis| file.reader.s16(base + 20 + axis * 2, "object AABB minimum") }
      maximum = 3.times.map { |axis| file.reader.s16(base + 26 + axis * 2, "object AABB maximum") }
      unless 3.times.all? { |axis| minimum[axis] <= maximum[axis] }
        raise ParseError, "#{file.label}: object #{object_index} AABB is inverted"
      end
      logical_size = 32 + part_count * 24
      file.require_zero_tail(chunk, logical_size, "object #{object_index}")
      parts = part_count.times.map do |part_index|
        offset = base + 32 + part_index * 24
        vertex_offset = file.reader.u32(offset, "object part vertex offset")
        vertex_count = file.reader.u16(offset + 4, "object part vertex count")
        vertex_destination = file.reader.u16(offset + 6, "object part vertex destination")
        index_offset = file.reader.u32(offset + 8, "object part index offset")
        index_count = file.reader.u16(offset + 12, "object part triangle index count")
        bone = file.reader.u16(offset + 14, "object part bone index")
        strips = 4.times.map { |strip| file.reader.u8(offset + 16 + strip, "object part strip count") }
        sequence_start = file.reader.u8(offset + 20, "object part sequence start")
        sequence_count = file.reader.u8(offset + 21, "object part sequence count")
        padding = file.reader.raw(offset + 22, 2, "object part padding")
        raise ParseError, "#{file.label}: object part padding is nonzero" unless padding == "\0\0".b
        unless vertex_offset % 32 == 0 && vertex_count.positive? && vertex_count.even? &&
               vertex_offset + vertex_count * 16 <= vertex_bytes &&
               vertex_destination + vertex_count <= 71
          raise ParseError, "#{file.label}: object part vertex range is invalid"
        end
        unless (index_count % 3).zero?
          raise ParseError, "#{file.label}: object part triangle index count is not divisible by three"
        end
        unless bone < bone_count
          raise ParseError, "#{file.label}: object part must bind exactly one joint in the 20-bone Quarrune rig"
        end
        first_zero = strips.index(0)
        if first_zero && strips[(first_zero + 1)..-1].to_a.any?(&:positive?)
          raise ParseError, "#{file.label}: object part strip counts contain a gap"
        end
        if sequence_count.positive? && (sequence_count < 3 || sequence_start + 3 * sequence_count > 70)
          raise ParseError, "#{file.label}: object part unindexed triangle sequence exceeds the vertex cache"
        end
        {
          object_name: name, vertex_offset: vertex_offset, vertex_count: vertex_count,
          vertex_destination: vertex_destination, index_offset: index_offset, index_count: index_count,
          strip_counts: strips, sequence_start: sequence_start, sequence_count: sequence_count,
          draws: index_count.positive? || strips.any?(&:positive?) || sequence_count.positive?
        }
      end
      unless parts.any? { |part| part[:draws] }
        raise ParseError, "#{file.label}: object #{object_index} has no drawing part"
      end
      source_vertices = parts.flat_map do |part|
        first = part[:vertex_offset] / 16
        (first...(first + part[:vertex_count])).to_a
      end
      positions = source_vertices.uniq.map do |vertex_index|
        pair_offset = vertex_chunk[:offset] + (vertex_index / 2) * 32
        position_offset = pair_offset + (vertex_index.odd? ? 8 : 0)
        3.times.map do |axis|
          file.reader.s16(position_offset + axis * 2, "object #{object_index} source vertex position")
        end
      end
      source_uvs_by_vertex = source_vertices.uniq.to_h do |vertex_index|
        pair_offset = vertex_chunk[:offset] + (vertex_index / 2) * 32
        uv_offset = pair_offset + (vertex_index.odd? ? 28 : 24)
        [vertex_index, [
          file.reader.s16(uv_offset, "object #{object_index} source vertex S"),
          file.reader.s16(uv_offset + 2, "object #{object_index} source vertex T")
        ]]
      end
      position_minimum = 3.times.map { |axis| positions.map { |position| position[axis] }.min }
      position_maximum = 3.times.map { |axis| positions.map { |position| position[axis] }.max }
      unless minimum == position_minimum && maximum == position_maximum
        raise ParseError, "#{file.label}: object #{object_index} AABB differs from its exact source vertices"
      end
      {
        name: name, material: material, triangle_count: triangle_count, parts: parts,
        minimum: minimum, maximum: maximum, source_vertices: source_vertices,
        source_uvs: source_uvs_by_vertex.values,
        source_uvs_by_vertex: source_uvs_by_vertex
      }
    end

    def validate_index_layout(file, chunk, objects)
      cursor = 0
      main_indices = 0
      objects.each_with_index do |object, object_index|
        loaded_slots = Set.new
        slot_sources = {}
        drawn_source_vertices = Set.new
        decoded_triangles = 0
        object[:parts].each do |part|
          part[:vertex_count].times do |offset|
            slot = part[:vertex_destination] + offset
            next unless slot < 70

            loaded_slots << slot
            slot_sources[slot] = part[:vertex_offset] / 16 + offset
          end
          unless part[:index_offset] == cursor
            raise ParseError, "#{file.label}: object-part index ranges are not writer-contiguous"
          end
          triangle_indices = file.reader.raw(
            chunk[:offset] + part[:index_offset], part[:index_count], "object-part triangle indices"
          )
          unless triangle_indices.each_byte.all? { |index| index < 70 && loaded_slots.include?(index) }
            raise ParseError, "#{file.label}: triangle index targets an unloaded Tiny3D vertex-cache slot"
          end
          triangle_indices.each_byte.each_slice(3) do |triangle|
            if triangle.uniq.length != 3
              raise ParseError, "#{file.label}: indexed draw contains a degenerate triangle"
            end
          end
          triangle_indices.each_byte { |slot| drawn_source_vertices << slot_sources.fetch(slot) }
          cursor += part[:index_count]
          main_indices += part[:index_count]
          decoded_triangles += part[:index_count] / 3

          sequence_slots = if part[:sequence_count].positive?
                             (part[:sequence_start]...(part[:sequence_start] + 3 * part[:sequence_count])).to_a
                           else
                             []
                           end
          unless sequence_slots.all? { |slot| slot < 70 && loaded_slots.include?(slot) }
            raise ParseError, "#{file.label}: unindexed triangle sequence targets an unloaded vertex-cache slot"
          end
          sequence_slots.each { |slot| drawn_source_vertices << slot_sources.fetch(slot) }
          decoded_triangles += part[:sequence_count]

          strip_groups = []
          part[:strip_counts].each do |count|
            break if count.zero?
            aligned_cursor = align(cursor, 8)
            internal_padding = file.reader.raw(
              chunk[:offset] + cursor, aligned_cursor - cursor, "strip-buffer alignment padding"
            )
            unless internal_padding.each_byte.all?(&:zero?)
              raise ParseError, "#{file.label}: strip-buffer alignment padding is nonzero"
            end
            cursor = aligned_cursor
            words = count.times.map do |word_index|
              file.reader.u16(chunk[:offset] + cursor + word_index * 2, "strip-buffer index")
            end
            strip_groups << words
            cursor += count * 2
          end
          strip_groups.each_with_index do |words, group_index|
            decoded_triangles += validate_strip_group(
              file, words, strip_groups[group_index..-1], loaded_slots
            )
            words.each { |word| drawn_source_vertices << slot_sources.fetch(word & 0x7FFF) }
          end
          if part[:draws]
            loaded_slots.clear
            slot_sources.clear
          end
        end
        unless decoded_triangles == object[:triangle_count]
          raise ParseError, "#{file.label}: object #{object_index} triangle count differs from its exact draw commands"
        end
        if drawn_source_vertices.empty?
          raise ParseError, "#{file.label}: object #{object_index} draw commands reach no source vertices"
        end
        object[:drawn_source_vertices] = drawn_source_vertices.to_a.sort
        object[:drawn_source_uvs] = object[:drawn_source_vertices].map do |vertex_index|
          object[:source_uvs_by_vertex].fetch(vertex_index)
        end
      end
      raise ParseError, "#{file.label}: totalIndexCount differs from object parts" unless main_indices == file.total_indices
      expected_span = align(cursor, 8)
      unless chunk[:size] == expected_span
        raise ParseError, "#{file.label}: I chunk size/padding differs from pinned writer layout"
      end
      file.require_zero_tail(chunk, cursor, "index chunk")
    end

    def parse_bvh(file, chunk, objects)
      object_count = objects.length
      base = chunk[:offset]
      node_count = file.reader.u16(base, "BVH node count")
      data_count = file.reader.u16(base + 2, "BVH data count")
      unless node_count.positive? && data_count == object_count
        raise ParseError, "#{file.label}: BVH counts do not cover the exact object set"
      end
      logical_size = 4 + node_count * 14 + data_count * 2
      file.require_zero_tail(chunk, logical_size, "BVH chunk")
      nodes = node_count.times.map do |index|
        offset = base + 4 + index * 14
        minimum = 3.times.map { |axis| file.reader.s16(offset + axis * 2, "BVH node AABB minimum") }
        maximum = 3.times.map { |axis| file.reader.s16(offset + 6 + axis * 2, "BVH node AABB maximum") }
        unless 3.times.all? { |axis| minimum[axis] <= maximum[axis] }
          raise ParseError, "#{file.label}: BVH node #{index} AABB is inverted"
        end
        {
          minimum: minimum, maximum: maximum,
          value: file.reader.u16(offset + 12, "BVH node value")
        }
      end
      data_base = base + 4 + node_count * 14
      data = data_count.times.map do |index|
        file.reader.u16(data_base + index * 2, "BVH object ordinal")
      end
      unless data.sort == (0...object_count).to_a
        raise ParseError, "#{file.label}: BVH data is not an exact object permutation"
      end

      visiting = Set.new
      seen_nodes = Set.new
      covered_data = Array.new(data_count, 0)
      visit = nil
      visit = lambda do |index|
        raise ParseError, "#{file.label}: BVH child index is out of range" unless index >= 0 && index < node_count
        if visiting.include?(index) || seen_nodes.include?(index)
          raise ParseError, "#{file.label}: BVH node graph repeats or cycles"
        end
        visiting << index
        seen_nodes << index
        value = nodes[index][:value]
        count = value & 0x0F
        signed_value = value >= 0x8000 ? value - 0x1_0000 : value
        offset = signed_value >> 4
        if count.zero?
          unless offset.positive? && index + offset + 1 < node_count
            raise ParseError, "#{file.label}: BVH internal-node child offset is invalid"
          end
          left = visit.call(index + offset)
          right = visit.call(index + offset + 1)
          expected_minimum = 3.times.map { |axis| [left[0][axis], right[0][axis]].min }
          expected_maximum = 3.times.map { |axis| [left[1][axis], right[1][axis]].max }
        else
          unless signed_value >= 0 && offset + count <= data_count
            raise ParseError, "#{file.label}: BVH leaf data range is invalid"
          end
          count.times { |position| covered_data[offset + position] += 1 }
          leaf_objects = count.times.map { |position| objects[data[offset + position]] }
          expected_minimum = 3.times.map { |axis| leaf_objects.map { |object| object[:minimum][axis] }.min }
          expected_maximum = 3.times.map { |axis| leaf_objects.map { |object| object[:maximum][axis] }.max }
        end
        unless nodes[index][:minimum] == expected_minimum && nodes[index][:maximum] == expected_maximum
          raise ParseError, "#{file.label}: BVH node #{index} AABB differs from its exact descendants"
        end
        visiting.delete(index)
        [expected_minimum, expected_maximum]
      end
      visit.call(0)
      raise ParseError, "#{file.label}: BVH contains unreachable nodes" unless seen_nodes.length == node_count
      raise ParseError, "#{file.label}: BVH leaf ranges overlap or omit data" unless covered_data.all? { |count| count == 1 }
      true
    end

    def validate_strip_group(file, words, suffix_groups, loaded_slots)
      raise ParseError, "#{file.label}: strip buffer is shorter than one triangle" if words.length < 3
      if (words.first & 0x8000) != 0
        raise ParseError, "#{file.label}: strip buffer begins with a restart marker"
      end
      indices = words.map { |word| word & 0x7FFF }
      unless indices.all? { |index| index < 70 && loaded_slots.include?(index) }
        raise ParseError, "#{file.label}: strip index targets an unloaded Tiny3D vertex-cache slot"
      end

      starts = [0]
      words.each_with_index do |word, index|
        starts << index if index.positive? && (word & 0x8000) != 0
      end
      starts << words.length
      triangles = 0
      starts.each_cons(2) do |left, right|
        segment = indices[left...right]
        raise ParseError, "#{file.label}: strip restart leaves fewer than three indices" if segment.length < 3
        segment.each_cons(3) do |triangle|
          if triangle.uniq.length != 3
            raise ParseError, "#{file.label}: strip contains a runtime-unsupported degenerate triangle"
          end
          triangles += 1
        end
      end

      suffix_indices = suffix_groups.flatten.map { |word| word & 0x7FFF }
      highest = suffix_indices.max
      free_vertices = 69 - highest
      capacity = 18 * free_vertices - (free_vertices.odd? ? 4 : 0)
      if words.length > capacity
        raise ParseError, "#{file.label}: strip buffer would overwrite a live Tiny3D vertex-cache slot"
      end
      triangles
    end

    def parse_materials(file, chunks)
      chunks.each_with_index.map do |chunk, index|
        base = chunk[:offset]
        file.require_zero_tail(chunk, 0x8C, "material #{index}")
        color_combiner = file.reader.u64(base, "material color combiner")
        other_mode_value = file.reader.u64(base + 8, "material other-mode value")
        other_mode_mask = file.reader.u64(base + 16, "material other-mode mask")
        blend_mode = file.reader.u32(base + 24, "material blend mode")
        draw_flags = file.reader.u32(base + 28, "material draw flags")
        raise ParseError, "#{file.label}: material #{index} reserved byte is nonzero" unless file.reader.u8(base + 0x20, "material reserved").zero?
        fog = file.reader.u8(base + 0x21, "material fog mode")
        flags = file.reader.u8(base + 0x22, "material color flags")
        vertex_fx = file.reader.u8(base + 0x23, "material vertex effect")
        prim_color = file.reader.raw(base + 0x24, 4, "material primitive color").bytes
        env_color = file.reader.raw(base + 0x28, 4, "material environment color").bytes
        blend_color = file.reader.raw(base + 0x2C, 4, "material blend color").bytes
        raise ParseError, "#{file.label}: material #{index} fog mode is invalid" unless fog <= 2
        raise ParseError, "#{file.label}: material #{index} color flags are invalid" unless flags <= 7
        raise ParseError, "#{file.label}: material #{index} vertex effect is invalid" unless vertex_fx <= 5
        name = file.string_at(file.reader.u32(base + 0x30, "material name"), "material #{index} name")
        textures = [0x34, 0x60].each_with_index.map do |relative, texture_index|
          texture = base + relative
          path_offset = file.reader.u32(texture + 4, "material texture path")
          texture_reference = file.reader.u32(texture, "material texture reference")
          texture_hash = file.reader.u32(texture + 8, "material texture hash")
          runtime_pointer = file.reader.u32(texture + 12, "material texture runtime pointer")
          width = file.reader.u16(texture + 16, "material texture width")
          height = file.reader.u16(texture + 18, "material texture height")
          raise ParseError, "#{file.label}: material texture runtime pointer is nonzero" unless runtime_pointer.zero?
          path = nil
          if path_offset.zero?
            unless texture_hash == texture_reference
              raise ParseError, "#{file.label}: unbound texture hash differs from its writer reference"
            end
            unless width <= 4096 && height <= 4096
              raise ParseError, "#{file.label}: unbound material texture dimensions are excessive"
            end
          else
            path = file.string_at(path_offset, "material #{index} texture #{texture_index} path")
            unless texture_reference.zero?
              raise ParseError, "#{file.label}: bound material texture must not also use a dynamic reference"
            end
            unless path.match?(/\Arom:\/[A-Za-z0-9][A-Za-z0-9._\/-]*\z/) && texture_hash == tiny3d_string_hash(path)
              raise ParseError, "#{file.label}: bound texture path/hash differs from pinned writer output"
            end
            unless width.positive? && height.positive? && width <= 4096 && height <= 4096
              raise ParseError, "#{file.label}: material texture dimensions are invalid"
            end
          end
          axes = [20, 32].map do |axis_offset|
            low = file.reader.f32(texture + axis_offset, "material tile low")
            high = file.reader.f32(texture + axis_offset + 4, "material tile high")
            mask = file.reader.s8(texture + axis_offset + 8, "material tile mask")
            shift = file.reader.s8(texture + axis_offset + 9, "material tile shift")
            mirror = file.reader.u8(texture + axis_offset + 10, "material tile mirror")
            clamp = file.reader.u8(texture + axis_offset + 11, "material tile clamp")
            unless low.finite? && high.finite? && shift.between?(-5, 10) && mirror <= 1 && clamp <= 1
              raise ParseError, "#{file.label}: material tile parameters are invalid"
            end
            { low: low, high: high, mask: mask, shift: shift, mirror: mirror, clamp: clamp }
          end
          {
            reference: texture_reference, path: path, hash: texture_hash,
            width: width, height: height, axes: axes
          }
        end
        {
          name: name, textures: textures, color_combiner: color_combiner,
          other_mode_value: other_mode_value, other_mode_mask: other_mode_mask,
          blend_mode: blend_mode, draw_flags: draw_flags, fog: fog,
          color_flags: flags, vertex_fx: vertex_fx, prim_color: prim_color,
          env_color: env_color, blend_color: blend_color
        }
      end
    end

    def parse_animation_chunk(file, chunk, index, bone_count)
      base = chunk[:offset]
      name = file.string_at(file.reader.u32(base, "animation #{index} name"), "animation #{index} name")
      duration = file.reader.f32(base + 4, "animation #{index} duration")
      keyframe_count = file.reader.u32(base + 8, "animation #{index} keyframe count")
      quaternion_channels = file.reader.u16(base + 12, "animation #{index} quaternion channels")
      scalar_channels = file.reader.u16(base + 14, "animation #{index} scalar channels")
      stream_path = file.string_at(file.reader.u32(base + 16, "animation #{index} stream path"), "animation #{index} stream path")
      unless duration.finite? && duration.positive? && duration <= 30.0
        raise ParseError, "#{file.label}: animation #{index} duration is invalid"
      end
      unless keyframe_count.positive? && keyframe_count <= MAX_KEYFRAMES
        raise ParseError, "#{file.label}: animation #{index} keyframe count is invalid"
      end
      channel_count = quaternion_channels + scalar_channels
      unless quaternion_channels.positive? && channel_count <= bone_count * 7
        raise ParseError, "#{file.label}: animation #{index} channel counts are invalid"
      end
      logical_size = 20 + channel_count * 12
      file.require_zero_tail(chunk, logical_size, "animation #{index}")
      unless stream_path == ANIMATION_ROM_PATHS[index]
        raise ParseError, "#{file.label}: animation #{index} embedded stream path is noncanonical"
      end

      mappings = channel_count.times.map do |channel|
        offset = base + 20 + channel * 12
        target = file.reader.u16(offset, "animation channel target")
        target_type = file.reader.u8(offset + 2, "animation channel type")
        attribute = file.reader.u8(offset + 3, "animation channel attribute")
        quant_scale_raw = file.reader.u32(offset + 4, "animation channel quant scale bits")
        quant_offset_raw = file.reader.u32(offset + 8, "animation channel quant offset bits")
        quant_scale = file.reader.f32(offset + 4, "animation channel quant scale")
        quant_offset = file.reader.f32(offset + 8, "animation channel quant offset")
        raise ParseError, "#{file.label}: animation channel targets a missing bone" unless target < bone_count
        if channel < quaternion_channels
          unless target_type == 3 && attribute.zero? && quant_scale_raw == 0xFF80_0000 && quant_offset_raw == 0x7F80_0000
            raise ParseError, "#{file.label}: quaternion channel mapping differs from pinned writer output"
          end
        else
          unless [0, 1].include?(target_type) && attribute <= 2 &&
                 quant_scale.finite? && quant_scale >= 0.0 && quant_offset.finite?
            raise ParseError, "#{file.label}: scalar channel mapping is invalid or runtime-unsupported"
          end
        end
        [target, target_type, attribute]
      end
      raise ParseError, "#{file.label}: animation channel mappings are duplicated" unless mappings.uniq.length == mappings.length
      {
        name: name, duration: duration, keyframe_count: keyframe_count,
        quaternion_channels: quaternion_channels, scalar_channels: scalar_channels,
        channel_count: channel_count, stream_path: stream_path
      }
    end

    def parse_stream(bytes, animation, label)
      raise ParseError, "#{label}: stream bytes are missing" unless bytes.is_a?(String)
      raise ParseError, "#{label}: stream is empty or excessive" if bytes.empty? || bytes.bytesize > MAX_FILE_BYTES
      reader = Reader.new(bytes.b, label)
      cursor = 0
      current_size = 8
      records = []
      animation[:keyframe_count].times do |index|
        tagged_ticks = reader.u16(cursor, "keyframe #{index} tagged ticks")
        channel = reader.u16(cursor + 2, "keyframe #{index} channel")
        first_value = reader.u16(cursor + 4, "keyframe #{index} value")
        second_value = current_size == 8 ? reader.u16(cursor + 6, "keyframe #{index} second value") : nil
        raise ParseError, "#{label}: keyframe #{index} channel is out of range" unless channel < animation[:channel_count]
        records << {
          size: current_size, tagged_ticks: tagged_ticks, ticks: tagged_ticks & 0x7FFF,
          large_next: (tagged_ticks & 0x8000) != 0, channel: channel,
          first_value: first_value, second_value: second_value
        }
        cursor += current_size
        current_size = (tagged_ticks & 0x8000).zero? ? 6 : 8
      end
      raise ParseError, "#{label}: stream has trailing bytes" unless cursor == bytes.bytesize
      quaternion_channels = animation[:quaternion_channels]
      records.each_with_index do |record, index|
        expected_size = if index.zero?
                          8
                        elsif record[:channel] < quaternion_channels
                          8
                        else
                          6
                        end
        raise ParseError, "#{label}: keyframe #{index} size flag chain disagrees with its channel" unless record[:size] == expected_size
        if record[:channel] < quaternion_channels
          packed = (record[:first_value] << 16) | record[:second_value].to_i
          raise ParseError, "#{label}: keyframe #{index} contains the forbidden zero quaternion" if packed.zero?
          unless packed_quaternion_valid?(packed)
            raise ParseError, "#{label}: keyframe #{index} quaternion decodes to an invalid runtime radicand"
          end
        elsif index.zero? && !record[:second_value].zero?
          raise ParseError, "#{label}: first scalar keyframe padding is nonzero"
        end
        next_channel = index + 1 < records.length ? records[index + 1][:channel] : record[:channel]
        expected_large = next_channel < quaternion_channels
        unless record[:large_next] == expected_large
          raise ParseError, "#{label}: keyframe #{index} next-size bit differs from pinned writer semantics"
        end
      end
      counts = Array.new(animation[:channel_count], 0)
      ticks = Array.new(animation[:channel_count], 0)
      writer_order = []
      records.each do |record|
        time_needed = ticks[record[:channel]]
        counts[record[:channel]] += 1
        ticks[record[:channel]] += record[:ticks]
        writer_order << [time_needed, ticks[record[:channel]], record[:channel]]
      end
      unless writer_order == writer_order.sort
        raise ParseError, "#{label}: keyframes differ from the pinned writer's global timeline order"
      end
      raise ParseError, "#{label}: every channel must have at least two keyframes" unless counts.all? { |count| count >= 2 }
      expected_ticks = (animation[:duration] * 60.0).round
      unless ticks.all? { |total| (total - expected_ticks).abs <= 1 }
        raise ParseError, "#{label}: per-channel tick coverage differs from animation duration"
      end
      true
    end

    def parse_binding(bytes, label)
      parse_ordered_binding(bytes, label, BINDING_KEYS)
    end

    def parse_runtime_binding(bytes, label)
      parse_ordered_binding(bytes, label, RUNTIME_BINDING_KEYS)
    end

    def parse_ordered_binding(bytes, label, expected_keys)
      raise ParseError, "#{label}: binding bytes are missing" unless bytes.is_a?(String)
      raise ParseError, "#{label}: binding has BOM" if bytes.start_with?("\xEF\xBB\xBF".b)
      raise ParseError, "#{label}: binding must use LF only" if bytes.include?("\r")
      unless bytes.end_with?("\n") && !bytes.end_with?("\n\n")
        raise ParseError, "#{label}: binding must have exactly one final LF"
      end
      utf8 = bytes.dup.force_encoding(Encoding::UTF_8)
      raise ParseError, "#{label}: binding is not valid UTF-8" unless utf8.valid_encoding?
      lines = utf8.split("\n", -1)
      lines.pop
      pairs = lines.map do |line|
        fields = line.split("\t", -1)
        raise ParseError, "#{label}: every row must contain exactly two TAB fields" unless fields.length == 2
        fields
      end
      keys = pairs.map(&:first)
      raise ParseError, "#{label}: binding keys/order differ" unless keys == expected_keys
      raise ParseError, "#{label}: binding contains an empty value" if pairs.any? { |pair| pair[1].empty? }
      pairs.to_h
    end

    def expected_runtime_binding(model_entries, build_id)
      by_path = model_entries.each_with_object({}) { |entry, values| values[entry[:path]] = entry }
      {
        "schema" => RUNTIME_BINDING_SCHEMA,
        "libdragon_commit" => N64Game::LibdragonSpriteContract::LIBDRAGON_COMMIT,
        "tiny3d_commit" => TINY3D_COMMIT,
        "runtime_helper_paths" => RUNTIME_HELPER_PATHS.join(","),
        "runtime_helper_bundle_sha256" => APPROVED_RUNTIME_HELPER_BUNDLE_SHA256,
        "production_id" => MODEL_PRODUCTION_ID,
        "body_sprite_path" => BODY_TEXTURE_PATH,
        "body_sprite_sha256" => by_path.fetch(BODY_TEXTURE_PATH)[:digest],
        "body_rom_path" => BODY_TEXTURE_ROM_PATH,
        "body_top_reference" => format("0x%08X", BODY_TOP_REFERENCE),
        "body_top_rect_px" => BODY_DYNAMIC_BINDINGS[0][:rect].join(","),
        "body_bottom_reference" => format("0x%08X", BODY_BOTTOM_REFERENCE),
        "body_bottom_rect_px" => BODY_DYNAMIC_BINDINGS[1][:rect].join(","),
        "body_reference_size_px" => "64,32",
        "body_upload_mode" => "surface_make_sub+rdpq_tex_upload+tlut_every_bind",
        "material_profile" => "TILE0_TEX0_X_SHADE_POINT",
        "accent_sprite_path" => ACCENT_TEXTURE_PATH,
        "accent_sprite_sha256" => by_path.fetch(ACCENT_TEXTURE_PATH)[:digest],
        "accent_rom_path" => ACCENT_TEXTURE_ROM_PATH,
        "blob_shadow_sprite_path" => BLOB_SHADOW_PATH,
        "blob_shadow_sprite_sha256" => by_path.fetch(BLOB_SHADOW_PATH)[:digest],
        "blob_shadow_rom_path" => BLOB_SHADOW_ROM_PATH,
        "blob_shadow_format" => "IA8",
        "blob_shadow_size_px" => "32,32",
        "footprint_mm" => "1250,800",
        "footprint_offset_mm" => "0,0",
        "base_opacity_q8" => "176",
        "build_id" => build_id
      }
    end

    def expected_binding(model_entries, animation_entries, signature, build_id)
      by_path = (model_entries + animation_entries).each_with_object({}) do |entry, values|
        values[entry[:path]] = entry
      end
      stream_payload = STREAM_SET_DOMAIN.dup
      ANIMATION_STREAM_PATHS.each do |path|
        digest = by_path.fetch(path)[:digest]
        stream_payload << [path.bytesize].pack("n") << path.b << [digest.bytesize].pack("n") << digest.b
      end
      {
        "schema" => BINDING_SCHEMA,
        "tiny3d_commit" => TINY3D_COMMIT,
        "model_production_id" => MODEL_PRODUCTION_ID,
        "animation_production_id" => ANIMATION_PRODUCTION_ID,
        "hero_model_path" => HERO_MODEL_PATH,
        "hero_model_sha256" => by_path.fetch(HERO_MODEL_PATH)[:digest],
        "distance_model_path" => DISTANCE_MODEL_PATH,
        "distance_model_sha256" => by_path.fetch(DISTANCE_MODEL_PATH)[:digest],
        "animation_header_path" => ANIMATION_HEADER_PATH,
        "animation_header_sha256" => by_path.fetch(ANIMATION_HEADER_PATH)[:digest],
        "animation_stream_set_sha256" => Digest::SHA256.hexdigest(stream_payload),
        "skeleton_signature_sha256" => signature,
        "bone_count" => QUARRUNE_BONE_COUNT.to_s,
        "animation_names" => ANIMATION_NAMES.join(","),
        "build_id" => build_id
      }
    end

    def align(value, alignment)
      remainder = value % alignment
      remainder.zero? ? value : value + alignment - remainder
    end

    def validate_chunk_alignments(file, alignments)
      file.chunks.each do |chunk|
        alignment = alignments[chunk[:type]]
        next unless alignment
        unless (chunk[:offset] % alignment).zero?
          raise ParseError, "#{file.label}: #{chunk[:type]} chunk offset is not #{alignment}-byte aligned"
        end
      end
    end

    def tiny3d_string_hash(value)
      value.b.each_byte.reduce(0x7E81_C0E9) do |hash, byte|
        ((hash >> 8) ^ ((hash << 24) & 0xFFFF_FFFF) ^ byte) & 0xFFFF_FFFF
      end
    end

    def packed_quaternion_valid?(packed)
      inverse_sqrt_two = 0.70710678118
      components = [
        (packed >> 20) & 0x3FF,
        (packed >> 10) & 0x3FF,
        packed & 0x3FF
      ].map do |value|
        value.to_f / 1023.0 * (inverse_sqrt_two * 2.0) - inverse_sqrt_two
      end
      radicand = 1.0 - components.sum { |component| component * component }
      radicand.finite? && radicand >= 0.0
    end
  end
end
