-- This Script is Part of the Prometheus Obfuscator by levno-710
--
-- WatermarkCheck.lua
--
-- This Script checks for watermarks in the code

local Step = require("prometheus.step");

local WatermarkCheck = Step:extend();
WatermarkCheck.Description = "This Step Checks for Watermarks";
WatermarkCheck.Name = "WatermarkCheck";

WatermarkCheck.SettingsDescriptor = {
	Watermark = {
		name = "Watermark",
		description = "The Watermark to check for",
		type = "string",
		default = "",
	},
}

function WatermarkCheck:init(_) end

function WatermarkCheck:apply(ast)
	return ast;
end

return WatermarkCheck;
