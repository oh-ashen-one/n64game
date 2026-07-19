# frozen_string_literal: true

require "set"

module N64Game
  # Bounds-checked reader for the exact uncompressed, lossless libdragon
  # sprite layout emitted by the pinned mksprite tool. Asset-compressed DCA,
  # lossy BC1Q/H264I, legacy, mipmapped, detail, tiled, and embedded-texparms
  # variants are intentionally outside this production contract.
  module LibdragonSpriteContract
    SCHEMA = "n64game-libdragon-sprite-contract-v1".freeze
    LIBDRAGON_COMMIT = "f13b48985edbf4310f07779c76d9a68c7605037b".freeze
    MAX_FILE_BYTES = 1024 * 1024
    HEADER_BYTES = 8
    EXT_BYTES = 128
    EXT_VERSION = 6
    FLAG_EXT = 0x80
    EXT_FLAG_FITS_TMEM = 0x20
    FORMATS = {
      8 => { name: "CI4", bits: 4, palette_colors: 16 },
      9 => { name: "CI8", bits: 8, palette_colors: 256 },
      13 => { name: "IA8", bits: 8, palette_colors: 0 }
    }.freeze

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

      def u16(offset, field)
        raw(offset, 2, field).unpack1("n")
      end

      def u32(offset, field)
        raw(offset, 4, field).unpack1("N")
      end
    end

    module_function

    def decode(bytes, label = "libdragon sprite")
      raise ParseError, "#{label}: bytes must be a String" unless bytes.is_a?(String)
      raise ParseError, "#{label}: file is shorter than the sprite header" if bytes.bytesize < HEADER_BYTES
      raise ParseError, "#{label}: file exceeds #{MAX_FILE_BYTES} bytes" if bytes.bytesize > MAX_FILE_BYTES
      raise ParseError, "#{label}: compressed DCA sprites are forbidden" if bytes.start_with?("DCA".b)
      if bytes.start_with?("\0\0\0\0BC1Q".b) || bytes.start_with?("\0\0\0\0H264".b)
        raise ParseError, "#{label}: lossy sprite containers are forbidden"
      end

      bytes = bytes.b
      reader = Reader.new(bytes, label)
      width = reader.u16(0, "width")
      height = reader.u16(2, "height")
      deprecated_bitdepth = reader.u8(4, "deprecated bitdepth")
      flags = reader.u8(5, "base flags")
      format_code = flags & 0x1F
      format = FORMATS[format_code]
      hslices = reader.u8(6, "horizontal slices")
      vslices = reader.u8(7, "vertical slices")

      unless width.positive? && height.positive? && width <= 1024 && height <= 1024
        raise ParseError, "#{label}: dimensions are outside the lossless sprite contract"
      end
      raise ParseError, "#{label}: deprecated bitdepth field is nonzero" unless deprecated_bitdepth.zero?
      raise ParseError, "#{label}: texture format is not CI4, CI8, or IA8" unless format
      unless flags == FLAG_EXT | format_code
        raise ParseError, "#{label}: base flags include runtime, no-data, or unsupported bits"
      end
      unless hslices == 1 && vslices == 1
        raise ParseError, "#{label}: production texture must be one untiled image"
      end

      row_bytes = ((width * format[:bits]) + 7) / 8
      pixel_bytes = row_bytes * height
      pixel_end = HEADER_BYTES + pixel_bytes
      ext_offset = align(pixel_end, 8)
      padding = reader.raw(pixel_end, ext_offset - pixel_end, "pixel alignment padding")
      raise ParseError, "#{label}: pixel alignment padding is nonzero" unless zero_bytes?(padding)
      reader.raw(ext_offset, EXT_BYTES, "extended header")

      ext_size = reader.u16(ext_offset, "extended-header size")
      version = reader.u16(ext_offset + 2, "extended-header version")
      palette_offset = reader.u32(ext_offset + 4, "palette offset")
      lod_bytes = reader.raw(ext_offset + 8, 56, "LOD table")
      ext_flags = reader.u16(ext_offset + 64, "extended flags")
      palette_used_raw = reader.u8(ext_offset + 66, "palette used-color count")
      ext_padding = reader.u8(ext_offset + 67, "extended-header padding")
      remaining_ext = reader.raw(ext_offset + 68, 60, "texture/detail/data-pointer fields")

      raise ParseError, "#{label}: extended-header size is not 128" unless ext_size == EXT_BYTES
      raise ParseError, "#{label}: extended-header version is not pinned version 6" unless version == EXT_VERSION
      raise ParseError, "#{label}: LOD table is nonzero" unless zero_bytes?(lod_bytes)
      raise ParseError, "#{label}: extended-header padding is nonzero" unless ext_padding.zero?
      unless zero_bytes?(remaining_ext)
        raise ParseError, "#{label}: texparms, detail texture, or redirected data pointer is present"
      end

      tmem_bytes = align(row_bytes, 8) * height
      tmem_bytes += 2048 if format[:palette_colors].positive?
      expected_ext_flags = tmem_bytes <= 4096 ? EXT_FLAG_FITS_TMEM : 0
      unless ext_flags == expected_ext_flags
        raise ParseError, "#{label}: FITS_TMEM flag differs from pinned mksprite calculation"
      end

      pixel_data = reader.raw(HEADER_BYTES, pixel_bytes, "pixel payload")
      palette = []
      palette_used = 0
      if format[:palette_colors].positive?
        expected_palette_offset = ext_offset + EXT_BYTES
        unless palette_offset == expected_palette_offset
          raise ParseError, "#{label}: palette offset differs from the no-LOD writer layout"
        end
        palette_bytes = format[:palette_colors] * 2
        expected_size = expected_palette_offset + palette_bytes
        raise ParseError, "#{label}: palette/file size differs from the full writer palette" unless bytes.bytesize == expected_size
        palette = format[:palette_colors].times.map do |index|
          reader.u16(palette_offset + index * 2, "palette color #{index}")
        end
        palette_used = palette_used_raw.zero? ? 256 : palette_used_raw
        unless palette_used.between?(1, format[:palette_colors])
          raise ParseError, "#{label}: palette used-color count exceeds its format"
        end
      else
        unless palette_offset.zero? && palette_used_raw.zero?
          raise ParseError, "#{label}: non-paletted sprite contains palette metadata"
        end
        raise ParseError, "#{label}: IA8 file has trailing bytes" unless bytes.bytesize == ext_offset + EXT_BYTES
      end

      indices = decode_indices(pixel_data, width, height, format_code, label)
      if format[:palette_colors].positive?
        maximum = indices.max
        unless maximum && maximum < palette_used && maximum + 1 == palette_used
          raise ParseError, "#{label}: pixel indices disagree with the writer used-color count"
        end
      end

      {
        schema: SCHEMA,
        libdragon_commit: LIBDRAGON_COMMIT,
        width: width,
        height: height,
        format: format[:name],
        format_code: format_code,
        row_bytes: row_bytes,
        pixel_bytes: pixel_bytes,
        pixel_data: pixel_data,
        indices: indices,
        palette: palette,
        palette_used: palette_used,
        tmem_bytes: tmem_bytes,
        fits_tmem: tmem_bytes <= 4096
      }
    rescue ParseError
      raise
    rescue StandardError => error
      raise ParseError, "#{label}: controlled sprite parse failure: #{error.class}: #{error.message}"
    end

    def validate_profile(bytes, label:, format:, width:, height:, fits_tmem:)
      decoded = decode(bytes, label)
      raise ParseError, "#{label}: format must be exactly #{format}" unless decoded[:format] == format
      unless decoded[:width] == width && decoded[:height] == height
        raise ParseError, "#{label}: dimensions must be exactly #{width}x#{height}"
      end
      unless decoded[:fits_tmem] == fits_tmem
        raise ParseError, "#{label}: TMEM-fit profile differs from the reviewed runtime path"
      end
      decoded
    end

    def decode_indices(pixel_data, width, height, format_code, label)
      case format_code
      when 9
        pixel_data.bytes
      when 8
        row_bytes = (width + 1) / 2
        indices = []
        height.times do |row|
          row_data = pixel_data.byteslice(row * row_bytes, row_bytes)
          row_data.each_byte.with_index do |byte, column|
            indices << (byte >> 4)
            if column * 2 + 1 < width
              indices << (byte & 0x0F)
            elsif (byte & 0x0F) != 0
              raise ParseError, "#{label}: odd-width CI4 row has a nonzero padding nibble"
            end
          end
        end
        indices
      else
        []
      end
    end

    def align(value, alignment)
      ((value + alignment - 1) / alignment) * alignment
    end

    def zero_bytes?(bytes)
      bytes.each_byte.all?(&:zero?)
    end
  end
end
