import argparse


def app():
	parser = argparse.ArgumentParser()
	parser.add_argument('--verbosity', help='increase output verbosity')
	args = parser.parse_args()

	if args.verbosity:
		print('verbosity turned onnn')
	else:
		print('not turned on')


if __name__ == '__main__':
	app()
