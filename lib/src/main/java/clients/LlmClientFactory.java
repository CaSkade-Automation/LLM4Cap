package clients;

import clients.gpt.GptClient;

public class LlmClientFactory {
	public static LlmClient getClient(LlmModels model) {
		switch (model) {
		
		case claude_3_5_sonnet_20240620:
		case claude_3_haiku_20240307:
		case claude_3_opus_20240229:
		case claude_3_sonnet_20240229:
			return new ClaudeClient(model);

		case gpt_4o:
		case gpt_4_turbo:
		case gpt_4:
		case gpt_3_5_turbo:
			return new GptClient(model);
		
		default:
			return new ClaudeClient(model);
		}
	}
}
